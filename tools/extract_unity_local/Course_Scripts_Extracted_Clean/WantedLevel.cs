using UnityEngine;
using UnityEngine.UI;

public class WantedLevel : MonoBehaviour
{
    public int currentWantedLevel = 0;
    public int maxWantedLevel = 5;
    public Image[] starImages;
    public Sprite filledStarSprite;
    public Sprite emptyStarSprite;

    public static WantedLevel Instance;

    private void Awake()
    {
        if (Instance == null) Instance = this;
    }

    public void AddWantedLevel(int amount = 1)
    {
        currentWantedLevel = Mathf.Clamp(currentWantedLevel + amount, 0, maxWantedLevel);
        UpdateStarsUI();
    }

    public void ClearWantedLevel()
    {
        currentWantedLevel = 0;
        UpdateStarsUI();
    }

    private void UpdateStarsUI()
    {
        if (starImages == null) return;

        for (int i = 0; i < starImages.Length; i++)
        {
            if (i < currentWantedLevel)
            {
                if (filledStarSprite != null) starImages[i].sprite = filledStarSprite;
                starImages[i].gameObject.SetActive(true);
            }
            else
            {
                if (emptyStarSprite != null) starImages[i].sprite = emptyStarSprite;
            }
        }
    }
}
