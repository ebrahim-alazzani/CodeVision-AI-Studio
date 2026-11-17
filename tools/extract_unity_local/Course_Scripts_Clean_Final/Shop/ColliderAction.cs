using UnityEngine;

namespace GTAViceCityClone.Shop
{
    /// <summary>
    /// ColliderAction detects player entry into shop zones and prompts or triggers the Shop UI.
    /// Reconstructed cleanly from Episodes 26, 27, 28, 29.
    /// </summary>
    public class ColliderAction : MonoBehaviour
    {
        [Header("Shop Reference")]
        public ShopSystem shopSystem;
        public GameObject interactionPromptUI;

        private bool playerInRange = false;

        private void Start()
        {
            if (shopSystem == null)
            {
                shopSystem = FindFirstObjectByType<ShopSystem>();
            }

            if (interactionPromptUI != null)
            {
                interactionPromptUI.SetActive(false);
            }
        }

        private void Update()
        {
            if (playerInRange && Input.GetKeyDown(KeyCode.E))
            {
                if (shopSystem != null)
                {
                    shopSystem.OpenShop();
                }
            }
        }

        private void OnTriggerEnter(Collider other)
        {
            if (other.CompareTag("Player"))
            {
                playerInRange = true;
                if (interactionPromptUI != null)
                {
                    interactionPromptUI.SetActive(true);
                }
            }
        }

        private void OnTriggerExit(Collider other)
        {
            if (other.CompareTag("Player"))
            {
                playerInRange = false;
                if (interactionPromptUI != null)
                {
                    interactionPromptUI.SetActive(false);
                }
                if (shopSystem != null)
                {
                    shopSystem.CloseShop();
                }
            }
        }
    }
}
