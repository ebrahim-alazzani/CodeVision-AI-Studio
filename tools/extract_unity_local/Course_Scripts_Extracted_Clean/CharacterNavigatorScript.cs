using UnityEngine;

[RequireComponent(typeof(CapsuleCollider))]
[RequireComponent(typeof(Rigidbody))]
public class CharacterNavigatorScript : MonoBehaviour
{
    [Header("Character Movement")]
    public float movingSpeed = 1.8f;
    public float turningSpeed = 300f;
    public float stopDistance = 1.2f;

    [Header("Obstacle Avoidance")]
    public float sensorLength = 2.5f;
    public float rayOffset = 0.4f;
    public LayerMask obstacleMask = ~0;
    public bool isAvoiding = false;

    [Header("Destination & Animation")]
    public Vector3 destination;
    public bool destinationReached;
    public Animator animator;

    [Header("Stuck Recovery")]
    public float maxStuckTime = 4.0f;
    private float stuckTimer = 0f;
    private Vector3 lastPosition;

    private Rigidbody rb;

    private void Awake()
    {
        animator = GetComponent<Animator>();
        if (animator == null) animator = GetComponentInChildren<Animator>();

        rb = GetComponent<Rigidbody>();
        if (rb == null) rb = gameObject.AddComponent<Rigidbody>();

        rb.mass = 60f;
        rb.linearDamping = 1f;
        rb.angularDamping = 0.05f;
        rb.constraints = RigidbodyConstraints.FreezeRotationX | RigidbodyConstraints.FreezeRotationZ;

        CapsuleCollider col = GetComponent<CapsuleCollider>();
        if (col != null)
        {
            col.center = new Vector3(0, 0.9f, 0);
            col.radius = 0.35f;
            col.height = 1.8f;
        }
    }

    private void Start()
    {
        lastPosition = transform.position;
    }

    private void Update()
    {
        CheckStuckStatus();
        WalkAndAvoid();
        UpdateAnimator();
    }

    public void WalkAndAvoid()
    {
        Vector3 destinationDirection = destination - transform.position;
        destinationDirection.y = 0f;
        float destinationDistance = destinationDirection.magnitude;

        if (destinationDistance <= stopDistance)
        {
            destinationReached = true;
            if (rb != null) rb.linearVelocity = new Vector3(0, rb.linearVelocity.y, 0);
            return;
        }

        destinationReached = false;

        Vector3 avoidanceVector = GetAvoidanceVector();
        Vector3 targetDirection = (avoidanceVector != Vector3.zero) ? avoidanceVector : destinationDirection.normalized;

        if (targetDirection != Vector3.zero)
        {
            Quaternion targetRotation = Quaternion.LookRotation(targetDirection);
            transform.rotation = Quaternion.RotateTowards(transform.rotation, targetRotation, turningSpeed * Time.deltaTime);
        }

        Vector3 moveVelocity = transform.forward * movingSpeed;
        if (rb != null)
        {
            rb.linearVelocity = new Vector3(moveVelocity.x, rb.linearVelocity.y, moveVelocity.z);
        }
        else
        {
            transform.Translate(Vector3.forward * movingSpeed * Time.deltaTime);
        }
    }

    private Vector3 GetAvoidanceVector()
    {
        isAvoiding = false;
        Vector3 avoidanceDir = Vector3.zero;

        Vector3 rayOrigin = transform.position + Vector3.up * 0.8f;
        RaycastHit hit;

        if (Physics.Raycast(rayOrigin, transform.forward, out hit, sensorLength, obstacleMask))
        {
            if (hit.transform != transform && !hit.collider.isTrigger)
            {
                isAvoiding = true;
                avoidanceDir += hit.normal * 2.0f;
            }
        }

        Vector3 rightOrigin = rayOrigin + transform.right * rayOffset;
        if (Physics.Raycast(rightOrigin, transform.forward, out hit, sensorLength, obstacleMask))
        {
            if (hit.transform != transform && !hit.collider.isTrigger)
            {
                isAvoiding = true;
                avoidanceDir -= transform.right * 1.5f;
            }
        }

        Vector3 leftOrigin = rayOrigin - transform.right * rayOffset;
        if (Physics.Raycast(leftOrigin, transform.forward, out hit, sensorLength, obstacleMask))
        {
            if (hit.transform != transform && !hit.collider.isTrigger)
            {
                isAvoiding = true;
                avoidanceDir += transform.right * 1.5f;
            }
        }

        return avoidanceDir.normalized;
    }

    private void CheckStuckStatus()
    {
        if (Vector3.Distance(transform.position, lastPosition) < 0.1f)
        {
            stuckTimer += Time.deltaTime;
            if (stuckTimer >= maxStuckTime)
            {
                destinationReached = true;
                stuckTimer = 0f;
            }
        }
        else
        {
            stuckTimer = 0f;
            lastPosition = transform.position;
        }
    }

    private void UpdateAnimator()
    {
        if (animator == null) return;

        float currentSpeed = destinationReached ? 0f : movingSpeed;
        animator.SetFloat("Speed", currentSpeed, 0.1f, Time.deltaTime);
        animator.SetFloat("InputMagnitude", destinationReached ? 0f : 1f, 0.1f, Time.deltaTime);
        animator.SetBool("IsGrounded", true);
    }

    public void LocateDestination(Vector3 targetDestination)
    {
        this.destination = targetDestination;
        destinationReached = false;
        stuckTimer = 0f;
    }
}
