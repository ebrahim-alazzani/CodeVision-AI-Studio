using UnityEngine;
using UnityEngine.UI;

public class ShopSystem : MonoBehaviour
{
    public GameObject shopUI;
    public Text playerMoneyText;
    public int playerMoney = 1000;

    public int riflePrice = 500;
    public GameObject rifleObject;
    public bool hasRifle = false;

    private void Start()
    {
        UpdateMoneyUI();
    }

    public void ToggleShopUI(bool isOpen)
    {
        if (shopUI != null)
        {
            shopUI.SetActive(isOpen);
            Cursor.lockState = isOpen ? CursorLockMode.None : CursorLockMode.Locked;
            Cursor.visible = isOpen;
        }
    }

    public void BuyRifle()
    {
        if (playerMoney >= riflePrice && !hasRifle)
        {
            playerMoney -= riflePrice;
            hasRifle = true;

            if (rifleObject != null)
            {
                rifleObject.SetActive(true);
            }

            UpdateMoneyUI();
        }
    }

    public void UpdateMoneyUI()
    {
        if (playerMoneyText != null)
        {
            playerMoneyText.text = "$" + playerMoney;
        }
    }
}
