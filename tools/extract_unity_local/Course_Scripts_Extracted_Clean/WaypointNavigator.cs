using UnityEngine;

public class WaypointNavigator : MonoBehaviour
{
    [Header("AI Character & Waypoint")]
    public CharacterNavigatorScript character;
    public WayPoint currentWaypoint;
    private int direction;

    private void Awake()
    {
        character = GetComponent<CharacterNavigatorScript>();
    }

    private void Start()
    {
        direction = Random.Range(0, 2);
        if (character != null && currentWaypoint != null)
        {
            character.LocateDestination(currentWaypoint.GetPosition());
        }
    }

    private void Update()
    {
        if (character == null) return;

        if (currentWaypoint == null)
        {
            currentWaypoint = FindObjectOfType<WayPoint>();
            if (currentWaypoint != null)
            {
                character.LocateDestination(currentWaypoint.GetPosition());
            }
            return;
        }

        if (character.destinationReached)
        {
            WayPoint next = null;

            if (direction == 0)
            {
                next = currentWaypoint.GetNextWaypoint();
                if (next == null)
                {
                    next = currentWaypoint.previousWaypoint;
                    direction = 1;
                }
            }
            else
            {
                next = currentWaypoint.previousWaypoint;
                if (next == null)
                {
                    next = currentWaypoint.GetNextWaypoint();
                    direction = 0;
                }
            }

            if (next != null)
            {
                currentWaypoint = next;
                character.LocateDestination(currentWaypoint.GetPosition());
            }
        }
    }
}
