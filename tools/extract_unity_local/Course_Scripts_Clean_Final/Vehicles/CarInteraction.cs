using UnityEngine;
using GTAViceCityClone.Player;
using GTAViceCityClone.CameraSystem;

namespace GTAViceCityClone.Vehicles
{
    /// <summary>
    /// CarInteraction manages entering and exiting player vehicles, camera switching, and input delegation.
    /// Reconstructed cleanly from Episodes 38, 39, 41.
    /// </summary>
    public class CarInteraction : MonoBehaviour
    {
        [Header("Vehicle References")]
        public CarController carController;
        public GameObject carCamera;
        public Transform exitPoint;
        public GameObject enterPromptUI;

        [Header("Interaction Settings")]
        public float enterDistance = 3.5f;
        public bool isPlayerInside = false;

        private GameObject playerObj;
        private PlayerManager playerManager;
        private CameraManager playerCameraManager;

        private void Start()
        {
            if (carController == null)
            {
                carController = GetComponent<CarController>();
            }

            if (carController != null)
            {
                carController.enabled = false;
            }

            if (carCamera != null)
            {
                carCamera.SetActive(false);
            }

            if (enterPromptUI != null)
            {
                enterPromptUI.SetActive(false);
            }

            playerObj = GameObject.FindGameObjectWithTag("Player");
            if (playerObj != null)
            {
                playerManager = playerObj.GetComponent<PlayerManager>();
                playerCameraManager = FindFirstObjectByType<CameraManager>();
            }
        }

        private void Update()
        {
            if (playerObj == null) return;

            float distanceToPlayer = Vector3.Distance(transform.position, playerObj.transform.position);

            if (!isPlayerInside)
            {
                // Show prompt if close enough
                bool inRange = distanceToPlayer <= enterDistance;
                if (enterPromptUI != null)
                {
                    enterPromptUI.SetActive(inRange);
                }

                // Check Enter Key
                if (inRange && (Input.GetKeyDown(KeyCode.F) || Input.GetKeyDown(KeyCode.E)))
                {
                    EnterVehicle();
                }
            }
            else
            {
                // Check Exit Key
                if (Input.GetKeyDown(KeyCode.F) || Input.GetKeyDown(KeyCode.E))
                {
                    ExitVehicle();
                }
            }
        }

        public void EnterVehicle()
        {
            isPlayerInside = true;

            if (enterPromptUI != null)
            {
                enterPromptUI.SetActive(false);
            }

            // Disable player on-foot controls and mesh
            if (playerManager != null)
            {
                playerManager.SetDrivingState(true);
            }

            playerObj.SetActive(false);

            // Enable Car Driving
            if (carController != null)
            {
                carController.enabled = true;
            }

            // Switch to Car Camera
            if (playerCameraManager != null)
            {
                playerCameraManager.gameObject.SetActive(false);
            }

            if (carCamera != null)
            {
                carCamera.SetActive(true);
            }
        }

        public void ExitVehicle()
        {
            isPlayerInside = false;

            // Stop Car
            if (carController != null)
            {
                carController.horizontalInput = 0f;
                carController.verticalInput = 0f;
                carController.isBraking = true;
                carController.enabled = false;
            }

            // Position Player at Exit Point
            Vector3 spawnPos = exitPoint != null ? exitPoint.position : transform.position + transform.right * 2f;
            playerObj.transform.position = spawnPos;
            playerObj.SetActive(true);

            if (playerManager != null)
            {
                playerManager.SetDrivingState(false);
            }

            // Switch back to Player Camera
            if (carCamera != null)
            {
                carCamera.SetActive(false);
            }

            if (playerCameraManager != null)
            {
                playerCameraManager.gameObject.SetActive(true);
            }
        }
    }
}
