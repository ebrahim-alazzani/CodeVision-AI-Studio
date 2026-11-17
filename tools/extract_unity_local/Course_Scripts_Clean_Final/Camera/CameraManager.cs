using UnityEngine;
using GTAViceCityClone.Player;

namespace GTAViceCityClone.CameraSystem
{
    /// <summary>
    /// CameraManager handles smooth following, spherical rotation, collision occlusion avoidance, aiming, and sniper scope.
    /// Reconstructed cleanly from Episodes 9, 10, 11, 12, 14, 28, 30, 57, 59, 64, 68, 71, 73.
    /// </summary>
    public class CameraManager : MonoBehaviour
    {
        [Header("Script References")]
        [SerializeField] private InputManager inputManager;
        [SerializeField] public Transform targetTransform;
        [SerializeField] public Transform cameraPivot;
        [SerializeField] public Transform cameraTransform;
        [SerializeField] private Camera cam;

        [Header("Collision Settings")]
        [SerializeField] private LayerMask collisionLayers;
        private float defaultPosition;
        private Vector3 cameraFollowVelocity = Vector3.zero;
        private Vector3 cameraVectorPosition;
        public float cameraCollisionRadius = 0.2f;
        public float cameraCollisionOffset = 0.2f;
        public float minCollisionOffset = 0.2f;

        [Header("Speed Settings")]
        public float cameraFollowSpeed = 0.2f;
        public float cameraLookSpeed = 2f;
        public float cameraPivotSpeed = 2f;

        [Header("Angle Limits")]
        public float minimumPivotAngle = -35f;
        public float maximumPivotAngle = 35f;

        [Header("Angles")]
        public float lookAngle;
        public float pivotAngle;

        [Header("Aiming & Scope Settings")]
        public bool isAiming;
        public bool isScoped;
        public GameObject scopeOverlay;
        public float defaultFOV = 60f;
        public float aimFOV = 40f;
        public float scopeFOV = 15f;
        public float fovTransitionSpeed = 10f;

        private void Awake()
        {
            if (targetTransform == null)
            {
                var player = GameObject.FindGameObjectWithTag("Player");
                if (player != null)
                {
                    targetTransform = player.transform;
                }
            }

            if (inputManager == null && targetTransform != null)
            {
                inputManager = targetTransform.GetComponent<InputManager>();
            }

            if (cameraTransform != null)
            {
                defaultPosition = cameraTransform.localPosition.z;
                cam = cameraTransform.GetComponent<Camera>();
            }
            else if (Camera.main != null)
            {
                cameraTransform = Camera.main.transform;
                defaultPosition = cameraTransform.localPosition.z;
                cam = Camera.main;
            }
        }

        public void HandleAllCameraMovement()
        {
            if (inputManager == null || targetTransform == null) return;

            FollowTarget();
            RotateCamera();
            HandleCameraCollisions();
            HandleZoom();
        }

        private void FollowTarget()
        {
            Vector3 targetPosition = Vector3.SmoothDamp(
                transform.position,
                targetTransform.position,
                ref cameraFollowVelocity,
                cameraFollowSpeed
            );
            transform.position = targetPosition;
        }

        private void RotateCamera()
        {
            lookAngle += (inputManager.cameraInputX * cameraLookSpeed);
            pivotAngle -= (inputManager.cameraInputY * cameraPivotSpeed);
            pivotAngle = Mathf.Clamp(pivotAngle, minimumPivotAngle, maximumPivotAngle);

            // Horizontal rotation on base object
            Vector3 rotation = Vector3.zero;
            rotation.y = lookAngle;
            Quaternion targetRotation = Quaternion.Euler(rotation);
            transform.rotation = targetRotation;

            // Vertical rotation on pivot child object
            rotation = Vector3.zero;
            rotation.x = pivotAngle;
            targetRotation = Quaternion.Euler(rotation);
            if (cameraPivot != null)
            {
                cameraPivot.localRotation = targetRotation;
            }
        }

        private void HandleCameraCollisions()
        {
            if (cameraTransform == null || cameraPivot == null) return;

            float targetPosition = defaultPosition;
            RaycastHit hit;
            Vector3 direction = cameraTransform.position - cameraPivot.position;
            direction.Normalize();

            if (Physics.SphereCast(cameraPivot.position, cameraCollisionRadius, direction, out hit, Mathf.Abs(targetPosition), collisionLayers))
            {
                float distance = Vector3.Distance(cameraPivot.position, hit.point);
                targetPosition = -(distance - cameraCollisionOffset);
            }

            if (Mathf.Abs(targetPosition) < minCollisionOffset)
            {
                targetPosition = -minCollisionOffset;
            }

            cameraVectorPosition.z = Mathf.Lerp(cameraTransform.localPosition.z, targetPosition, 0.2f);
            cameraTransform.localPosition = cameraVectorPosition;
        }

        private void HandleZoom()
        {
            if (cam == null) return;

            isAiming = inputManager.aimInput;

            float targetFOV = defaultFOV;
            if (isScoped)
            {
                targetFOV = scopeFOV;
            }
            else if (isAiming)
            {
                targetFOV = aimFOV;
            }

            cam.fieldOfView = Mathf.Lerp(cam.fieldOfView, targetFOV, Time.deltaTime * fovTransitionSpeed);
        }

        public void ToggleScope()
        {
            isScoped = !isScoped;
            if (scopeOverlay != null)
            {
                scopeOverlay.SetActive(isScoped);
            }
        }

        public void SetScope(bool active)
        {
            isScoped = active;
            if (scopeOverlay != null)
            {
                scopeOverlay.SetActive(isScoped);
            }
        }
    }
}
