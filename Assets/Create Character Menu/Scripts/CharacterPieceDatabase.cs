using Sirenix.OdinInspector;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public enum CharacterPieceType { Body, Eyes, Outfit, Hairstyle, Accessory}
public class CharacterPieceDatabase : MonoBehaviour
{
    public static CharacterPieceDatabase Instance;

    [field: SerializeField, ReadOnly] public CharacterTypeSO ActiveCharacterType { get; private set; }
    [field: SerializeField] public CharacterTypeSO[] CharacterTypes { get; private set; }

    public const string CharacterPiecesFolderName = "Character Pieces";
    public const string SavedCharactersFolderName = "Saved Characters";
    public static string SavedCharactersDirectory { get; private set; }
    public static string CharacterPiecesDirectory { get; private set; }

    public event EventHandler<CharacterTypeSO> OnActiveCharacterTypeChanged;

    private void Awake()
    {
        SavedCharactersDirectory = Path.Combine(Application.persistentDataPath, SavedCharactersFolderName);
        TryResolveCharacterPiecesDirectory(out _);

        foreach (CharacterTypeSO characterType in CharacterTypes)
        {
            characterType.Init();
        }

        ActiveCharacterType = CharacterTypes[0];

        Instance = this;
    }

    // Ищет папку "Character Pieces" в нескольких местах, чтобы работало и в редакторе,
    // и в собранном билде (особенно macOS .app, где Data лежит внутри bundle).
    // Порядок кандидатов: cwd → Assets → Assets/Create Character Menu → StreamingAssets →
    // persistentDataPath → и вверх от dataPath (Resources, Contents, сам .app, папка рядом с .app).
    // Основано на PR #3 (JohanJimenex), расширено кандидатом "рядом с .app" для двойного клика.
    public static bool TryResolveCharacterPiecesDirectory(out string resolvedPath)
    {
        if (!string.IsNullOrWhiteSpace(CharacterPiecesDirectory) && Directory.Exists(CharacterPiecesDirectory))
        {
            resolvedPath = CharacterPiecesDirectory;
            return true;
        }

        var candidatePaths = new List<string>
        {
            Path.Combine(Directory.GetCurrentDirectory(), CharacterPiecesFolderName),
            Path.Combine(Application.dataPath, CharacterPiecesFolderName),
            Path.Combine(Application.dataPath, "Create Character Menu", CharacterPiecesFolderName),
            Path.Combine(Application.streamingAssetsPath, CharacterPiecesFolderName),
            Path.Combine(Application.persistentDataPath, CharacterPiecesFolderName),
        };

        // В player-билдах dataPath спрятан глубоко в bundle. Поднимаемся вверх,
        // чтобы найти "Character Pieces" в Resources, Contents, самом .app или рядом с ним.
        string current = Application.dataPath;
        for (int i = 0; i < 4 && !string.IsNullOrWhiteSpace(current); i++)
        {
            current = Path.GetDirectoryName(current);
            if (!string.IsNullOrWhiteSpace(current))
                candidatePaths.Add(Path.Combine(current, CharacterPiecesFolderName));
        }

        var checkedPaths = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (string candidatePath in candidatePaths)
        {
            if (string.IsNullOrWhiteSpace(candidatePath))
                continue;

            string normalizedPath;
            try { normalizedPath = Path.GetFullPath(candidatePath); }
            catch { continue; }

            if (!checkedPaths.Add(normalizedPath))
                continue;

            if (Directory.Exists(normalizedPath))
            {
                CharacterPiecesDirectory = normalizedPath;
                resolvedPath = normalizedPath;
                return true;
            }
        }

        resolvedPath = string.Empty;
        return false;
    }

public void SetActiveCharacterType(CharacterTypeSO characterType)
    {
        if (characterType == ActiveCharacterType) return;

        //Debug.Log("Set New Character Type");
        ActiveCharacterType = characterType;

        OnActiveCharacterTypeChanged?.Invoke(this, ActiveCharacterType);
    }

    private void OnDestroy()
    {
        foreach (CharacterTypeSO characterType in CharacterTypes)
        {
            characterType.ClearSprites();
            characterType.SaveRandomizeToggles();
        }
    }

    [System.Serializable]
    public class CharacterPieceCollection
    {
        public CharacterPieceType CollectionName;
        public List<Sprite> Sprites;
    }
}