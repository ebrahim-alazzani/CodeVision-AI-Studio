using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using GTAViceCityClone.Player;
using GTAViceCityClone.Shooting;
using GTAViceCityClone.Data;

namespace GTAViceCityClone.UI
{
    /// <summary>
    /// GameManager maintains global game state, money economy, active missions, and save/load coordinates.
    /// Reconstructed cleanly from Episodes 23, 26, 27, 28, 29, 30, 31, 33, 42, 45, 50, 59, 60, 61, 62, 63, 64, 65, 66, 67, 70.
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        [Header("Economy")]
        public int playerMoney = 1500;
        public Text moneyText;

        [Header("Mission Tracking")]
        public int currentMissionIndex = 0;

        [Header("Player Components Reference")]
        public PlayerMovement playerMovement;
        public PlayerHealth playerHealth;
        public ShootingController shootingController;

        [Header("Game Over UI")]
        public GameObject gameOverPanel;

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
            if (playerMovement == null) playerMovement = FindFirstObjectByType<PlayerMovement>();
            if (playerHealth == null) playerHealth = FindFirstObjectByType<PlayerHealth>();
            if (shootingController == null) shootingController = FindFirstObjectByType<ShootingController>();

            if (gameOverPanel != null)
            {
                gameOverPanel.SetActive(false);
            }

            UpdateMoneyUI();
        }

        public void AddMoney(int amount)
        {
            playerMoney += amount;
            UpdateMoneyUI();
        }

        public bool CanAfford(int amount)
        {
            return playerMoney >= amount;
        }

        public bool DeductMoney(int amount)
        {
            if (CanAfford(amount))
            {
                playerMoney -= amount;
                UpdateMoneyUI();
                return true;
            }
            return false;
        }

        public void UpdateMoneyUI()
        {
            if (moneyText != null)
            {
                moneyText.text = $"${playerMoney}";
            }
        }

        public void SaveGame()
        {
            SaveSystem.SavePlayer(playerMovement, playerHealth, this, shootingController);
        }

        public void LoadGame()
        {
            PlayerData data = SaveSystem.LoadPlayer();
            if (data == null) return;

            playerMoney = data.money;
            currentMissionIndex = data.currentMission;
            UpdateMoneyUI();

            if (playerMovement != null)
            {
                Vector3 loadedPos = new Vector3(data.position[0], data.position[1], data.position[2]);
                playerMovement.transform.position = loadedPos;
            }

            if (playerHealth != null)
            {
                playerHealth.SetHealthDirect(data.health);
            }

            if (shootingController != null)
            {
                shootingController.SelectWeapon(data.currentWeaponIndex);
                shootingController.currentAmmo = data.currentAmmo;
            }
        }

        public void OnPlayerDied()
        {
            if (gameOverPanel != null)
            {
                gameOverPanel.SetActive(true);
            }
        }

        public void RestartGame()
        {
            Time.timeScale = 1f;
            SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
        }
    }
}
