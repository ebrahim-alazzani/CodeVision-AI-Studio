using UnityEngine;

namespace GTAViceCityClone.Missions
{
    /// <summary>
    /// Diaz NPC behavior for storyline cutscenes and mission objectives.
    /// Reconstructed cleanly from Episode 62.
    /// </summary>
    public class Diaz : Character
    {
        [Header("Diaz Specifics")]
        public Transform mansionThronePoint;

        public override void Die()
        {
            base.Die();
            Debug.Log("Diaz has been eliminated!");
        }
    }
}
