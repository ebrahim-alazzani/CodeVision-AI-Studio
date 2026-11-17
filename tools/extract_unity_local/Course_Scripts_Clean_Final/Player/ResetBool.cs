using UnityEngine;

namespace GTAViceCityClone.Player
{
    /// <summary>
    /// ResetBool is a StateMachineBehaviour attached to Animator states to reset boolean parameters.
    /// Reconstructed cleanly from Episodes 14, 15.
    /// </summary>
    public class ResetBool : StateMachineBehaviour
    {
        public string targetBool = "isInteracting";
        public bool status = false;

        public override void OnStateEnter(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            animator.SetBool(targetBool, status);
        }
    }
}
