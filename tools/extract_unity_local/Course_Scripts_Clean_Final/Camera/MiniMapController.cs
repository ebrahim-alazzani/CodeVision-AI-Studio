using UnityEngine;

namespace GTAViceCityClone.CameraSystem
{
    /// <summary>
    /// MiniMapController keeps a top-down orthographic camera directly centered over the player.
    /// Reconstructed cleanly from Episode 52.
    /// </summary>
    public class MiniMapController : MonoBehaviour
    {
        [Header("Target Settings")]
        public Transform player;
        public float heightOffset = 30f;
        public bool rotateWithPlayer = true;

        private void Start()
        {
            if (player == null)
            {
                var playerObj = GameObject.FindGameObjectWithTag("Player");
                if (playerObj != null)
                {
                    player = playerObj.transform;
                }
            }
        }

        private void LateUpdate()
        {
            if (player == null) return;

            // Follow player position in X and Z
            Vector3 newPosition = player.position;
            newPosition.y = transform.position.y;
            if (heightOffset > 0f)
            {
                newPosition.y = player.position.y + heightOffset;
            }
            transform.position = newPosition;

            // Follow player rotation if enabled
            if (rotateWithPlayer)
            {
                transform.rotation = Quaternion.Euler(90f, player.eulerAngles.y, 0f);
            }
            else
            {
                transform.rotation = Quaternion.Euler(90f, 0f, 0f);
            }
        }
    }
}
