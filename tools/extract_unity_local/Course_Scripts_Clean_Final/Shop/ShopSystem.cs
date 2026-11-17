using UnityEngine;
using UnityEngine.UI;
using GTAViceCityClone.UI;
using GTAViceCityClone.Shooting;

namespace GTAViceCityClone.Shop
{
    /// <summary>
    /// ShopSystem manages the weapon shop UI, purchasing rifles/ammo, and deducting player money.
    /// Reconstructed cleanly from Episodes 26, 27, 28, 29, 74.
    /// </summary>
    public class ShopSystem : MonoBehaviour
    {
        [Header("Shop UI Panel")]
        public GameObject shopPanel;

        [Header("Weapon Prices")]
        public int pistolPrice = 250;
        public int smgPrice = 750;
        public int riflePrice = 1500;
        public int ammoPrice = 100;
        public int ammoCountPerPack = 60;

        [Header("Weapon Status")]
        public bool hasPistol = true;
        public bool hasSMG = false;
        public bool hasRifle = false;

        [Header("Player References")]
        public ShootingController playerShooting;

        private void Start()
        {
            if (shopPanel != null)
            {
                shopPanel.SetActive(false);
            }

            if (playerShooting == null)
            {
                var player = GameObject.FindGameObjectWithTag("Player");
                if (player != null)
                {
                    playerShooting = player.GetComponent<ShootingController>();
                }
            }
        }

        public void OpenShop()
        {
            if (shopPanel != null)
            {
                shopPanel.SetActive(true);
                Cursor.lockState = CursorLockMode.None;
                Cursor.visible = true;
            }
        }

        public void CloseShop()
        {
            if (shopPanel != null)
            {
                shopPanel.SetActive(false);
                Cursor.lockState = CursorLockMode.Locked;
                Cursor.visible = false;
            }
        }

        public void BuySMG()
        {
            if (hasSMG)
            {
                if (playerShooting != null) playerShooting.SelectWeapon(1);
                return;
            }

            if (GameManager.Instance != null && GameManager.Instance.CanAfford(smgPrice))
            {
                GameManager.Instance.DeductMoney(smgPrice);
                hasSMG = true;
                if (playerShooting != null)
                {
                    playerShooting.SelectWeapon(1);
                }
            }
        }

        public void BuyRifle()
        {
            if (hasRifle)
            {
                if (playerShooting != null) playerShooting.SelectWeapon(2);
                return;
            }

            if (GameManager.Instance != null && GameManager.Instance.CanAfford(riflePrice))
            {
                GameManager.Instance.DeductMoney(riflePrice);
                hasRifle = true;
                if (playerShooting != null)
                {
                    playerShooting.SelectWeapon(2);
                }
            }
        }

        public void BuyAmmo()
        {
            if (GameManager.Instance != null && GameManager.Instance.CanAfford(ammoPrice))
            {
                GameManager.Instance.DeductMoney(ammoPrice);
                if (playerShooting != null)
                {
                    playerShooting.AddAmmo(ammoCountPerPack);
                }
            }
        }
    }
}
