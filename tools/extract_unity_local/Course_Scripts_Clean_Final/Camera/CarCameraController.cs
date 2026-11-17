using UnityEngine;

namespace GTAViceCityClone.CameraSystem
{
    /// <summary>
    /// CarCameraController provides a smooth third-person trailing camera for vehicles.
    /// Reconstructed cleanly from Episodes 40, 72, 75.
    /// </summary>
    public class CarCameraController : MonoBehaviour
    {
        [Header("Target Settings")]
        public Transform carTransform;
        public float distance = 6.0f;
        public float height = 2.5f;
        public float heightDamping = 2.0f;
        public float rotationDamping = 3.0f;

        [Header("Look Angle Offset")]
        public float lookAtHeight = 1.0f;

        private void LateUpdate()
        {
            if (carTransform == null) return;

            // Calculate target rotation and height
            float wantedRotationAngle = carTransform.eulerAngles.y;
            float wantedHeight = carTransform.position.y + height;

            float currentRotationAngle = transform.eulerAngles.y;
            float currentHeight = transform.position.y;

            // Damp the rotation and height
            currentRotationAngle = Mathf.LerpAngle(currentRotationAngle, wantedRotationAngle, rotationDamping * Time.deltaTime);
            currentHeight = Mathf.Lerp(currentHeight, wantedHeight, heightDamping * Time.deltaTime);

            // Convert angle into rotation
            Quaternion currentRotation = Quaternion.Euler(0f, currentRotationAngle, 0f);

            // Position camera behind target
            Vector3 targetPosition = carTransform.position;
            targetPosition -= currentRotation * Vector3.forward * distance;
            targetPosition.y = currentHeight;

            transform.position = targetPosition;

            // Always look at car target
            Vector3 lookTarget = carTransform.position + Vector3.up * lookAtHeight;
            transform.LookAt(lookTarget);
        }

        public void SetTarget(Transform newTarget)
        {
            carTransform = newTarget;
        }
    }
}
