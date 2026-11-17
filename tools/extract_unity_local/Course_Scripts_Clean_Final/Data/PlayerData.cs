using System;
using GTAViceCityClone.Player;
using GTAViceCityClone.UI;
using GTAViceCityClone.Shooting;

namespace GTAViceCityClone.Data
{
    /// <summary>
    /// PlayerData holds serializable game state for saving and loading player progress.
    /// Reconstructed cleanly from Episode 65.
    /// </summary>
    [Serializable]
    public class PlayerData
    {
        public float[] position = new float[3];
        public float health;
        public int money;
        public int currentMission;
        public int currentWeaponIndex;
        public int currentAmmo;

        public PlayerData(PlayerMovement player, PlayerHealth playerHealth, GameManager gameManager, ShootingController shooting)
        {
            if (player != null)
            {
                position[0] = player.transform.position.x;
                position[1] = player.transform.position.y;
                position[2] = player.transform.position.z;
            }

            if (playerHealth != null)
            {
                health = playerHealth.currentHealth;
            }
            else
            {
                health = 100f;
            }

            if (gameManager != null)
            {
                money = gameManager.playerMoney;
                currentMission = gameManager.currentMissionIndex;
            }

            if (shooting != null)
            {
                currentWeaponIndex = shooting.currentWeaponIndex;
                currentAmmo = shooting.currentAmmo;
            }
        }
    }
}
