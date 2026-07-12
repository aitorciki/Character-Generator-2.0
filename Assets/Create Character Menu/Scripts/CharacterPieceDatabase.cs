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

    // Looks for the "Character Pieces" folder in several locations, so it works both in the
    // editor and in a built player (especially the macOS .app, where Data lives inside the bundle).
    // Candidate order: cwd -> Assets -> Assets/Create Character Menu -> StreamingAssets ->
    // persistentDataPath -> and walking up from dataPath (Resources, Contents, the .app itself,
    // and the folder next to the .app).
    // Based on PR #3 (JohanJimenex), extended with the "next to the .app" candidate for double-click launch.
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

        // In player builds dataPath is buried deep inside the bundle. Walk upwards to
        // find "Character Pieces" in Resources, Contents, the .app itself, or next to it.
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