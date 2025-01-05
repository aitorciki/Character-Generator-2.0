using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(fileName ="Animation Data", menuName ="Animation Data")]
public class AnimationSO : ScriptableObject
{
    public string AnimationName;
    public Vector2Int AnimationStartPosition;
    public Vector2Int AnimationPositionOffset;

    [Space]

    public Vector2Int AnimationStartPosition32x32;
    public Vector2Int AnimationPositionOffset32x32;

    [Space]

    public Vector2Int AnimationStartPosition48x48;
    public Vector2Int AnimationPositionOffset48x48;
}