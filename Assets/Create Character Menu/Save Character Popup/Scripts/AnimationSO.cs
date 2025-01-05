using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(fileName ="Animation Data", menuName ="Animation Data")]
public class AnimationSO : ScriptableObject
{
    public string AnimationName;
    public Vector2Int AnimationStartPosition;
    public Vector2Int AnimationPositionOffset;
}