using UnityEngine;

public class AnimatorManager : MonoBehaviour
{
    public Animator animator;
    int vertical;
    int horizontal;

    private void Awake()
    {
        animator = GetComponent<Animator>();
        vertical = Animator.StringToHash("Vertical");
        horizontal = Animator.StringToHash("Horizontal");
    }

    public void PlayTargetAnim(string targetAnim, bool isInteracting)
    {
        if (animator == null) return;
        animator.SetBool("isInteracting", isInteracting);
        animator.CrossFade(targetAnim, 0.2f);
    }

    public void UpdateAnimValues(float horizontalMovement, float verticalMovement, bool isSprinting)
    {
        float snappedHorizontal = 0;
        float snappedVertical = 0;

        #region Horizontal Snapping
        if (horizontalMovement > 0 && horizontalMovement < 0.55f)
            snappedHorizontal = 0.5f;
        else if (horizontalMovement > 0.55f)
            snappedHorizontal = 1f;
        else if (horizontalMovement < 0 && horizontalMovement > -0.55f)
            snappedHorizontal = -0.5f;
        else if (horizontalMovement < -0.55f)
            snappedHorizontal = -1f;
        else
            snappedHorizontal = 0;
        #endregion

        #region Vertical Snapping
        if (verticalMovement > 0 && verticalMovement < 0.55f)
            snappedVertical = 0.5f;
        else if (verticalMovement > 0.55f)
            snappedVertical = 1f;
        else if (verticalMovement < 0 && verticalMovement > -0.55f)
            snappedVertical = -0.5f;
        else if (verticalMovement < -0.55f)
            snappedVertical = -1f;
        else
            snappedVertical = 0;
        #endregion

        if (isSprinting && snappedVertical > 0)
        {
            snappedVertical = 2f;
        }

        if (animator != null)
        {
            animator.SetFloat(horizontal, snappedHorizontal, 0.1f, Time.deltaTime);
            animator.SetFloat(vertical, snappedVertical, 0.1f, Time.deltaTime);
        }
    }
}
