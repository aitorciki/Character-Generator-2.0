using Sirenix.OdinInspector;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using TMPro;
using UnityEngine;

public class AnimationDataDropdown : MonoBehaviour
{


    [SerializeField, ReadOnly] AnimationSO selectedAnimation;

    [SerializeField] AnimationSO[] availableAnimations;

    [Space]

    [SerializeField] TMP_Dropdown animationDropdown;
    private void Awake()
    {
        animationDropdown.ClearOptions();
        animationDropdown.options.Add(new TMP_Dropdown.OptionData() { text = "Entire Spritesheet" });

        foreach (var animation in availableAnimations)
        {
            animationDropdown.options.Add(new TMP_Dropdown.OptionData() { text = animation.AnimationName });
        }
    }

    public AnimationSO RefreshSelectedAnimation()
    {
        var dropdownOptions = animationDropdown.options.Select(option => option.text).ToList();

        if (animationDropdown.value <= 0)
        {
            selectedAnimation = null;
        }
        else
        {
            selectedAnimation = availableAnimations[animationDropdown.value - 1];
        }
        return selectedAnimation;

        //var matchingAnimations = availableAnimations.Where(animation => dropdownOptions.Contains(animation.AnimationName)).ToList();
        //return selectedAnimation = availableAnimations.First(animation => dropdownOptions.Contains(animation.AnimationName));
    }
}