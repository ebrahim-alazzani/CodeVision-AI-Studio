using UnityEngine;
using UnityEngine.UI;

namespace GTAViceCityClone.UI
{
    /// <summary>
    /// HealthBar updates the UI slider and health color gradient.
    /// Reconstructed cleanly from Episode 49.
    /// </summary>
    public class HealthBar : MonoBehaviour
    {
        public Slider slider;
        public Gradient gradient;
        public Image fill;

        public void SetMaxHealth(float maxHealth)
        {
            if (slider != null)
            {
                slider.maxValue = maxHealth;
                slider.value = maxHealth;
            }

            if (fill != null && gradient != null)
            {
                fill.color = gradient.Evaluate(1f);
            }
        }

        public void SetHealth(float health)
        {
            if (slider != null)
            {
                slider.value = health;
            }

            if (fill != null && gradient != null)
            {
                fill.color = gradient.Evaluate(slider.normalizedValue);
            }
        }
    }
}
