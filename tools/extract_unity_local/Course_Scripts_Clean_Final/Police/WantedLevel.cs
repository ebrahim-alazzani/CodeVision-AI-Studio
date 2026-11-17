using UnityEngine;
using UnityEngine.UI;

namespace GTAViceCityClone.Police
{
    /// <summary>
    /// WantedLevel tracks the player's crime rating (0-5 stars), UI star display, and cool-down timer.
    /// Reconstructed cleanly from Episodes 42, 44, 45, 46, 51.
    /// </summary>
    public class WantedLevel : MonoBehaviour
    {
        public static WantedLevel Instance { get; private set; }

        [Header("Wanted Stars (0 - 5)")]
        [Range(0, 5)] public int currentWantedLevel = 0;
        public GameObject[] starIcons;

        [Header("Cool Down Settings")]
        public float decayTimer = 25f;
        private float currentTimer;
        public bool playerUnderObservation = false;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
        }

        private void Start()
        {
            UpdateStarUI();
            currentTimer = decayTimer;
        }

        private void Update()
        {
            if (currentWantedLevel > 0 && !playerUnderObservation)
            {
                currentTimer -= Time.deltaTime;
                if (currentTimer <= 0f)
                {
                    ReduceWantedLevel(1);
                    currentTimer = decayTimer;
                }
            }
        }

        public void ReportCrime(int starsToAdd)
        {
            currentWantedLevel = Mathf.Clamp(currentWantedLevel + starsToAdd, 0, 5);
            currentTimer = decayTimer;
            UpdateStarUI();
        }

        public void ReduceWantedLevel(int amount)
        {
            currentWantedLevel = Mathf.Clamp(currentWantedLevel - amount, 0, 5);
            UpdateStarUI();
        }

        public void ClearWantedLevel()
        {
            currentWantedLevel = 0;
            UpdateStarUI();
        }

        private void UpdateStarUI()
        {
            if (starIcons == null || starIcons.Length == 0) return;

            for (int i = 0; i < starIcons.Length; i++)
            {
                if (starIcons[i] != null)
                {
                    starIcons[i].SetActive(i < currentWantedLevel);
                }
            }
        }
    }
}
