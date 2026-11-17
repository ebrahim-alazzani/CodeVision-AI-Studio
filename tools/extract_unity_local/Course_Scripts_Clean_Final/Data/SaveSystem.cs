using System.IO;
using System.Runtime.Serialization.Formatters.Binary;
using UnityEngine;
using GTAViceCityClone.Player;
using GTAViceCityClone.UI;
using GTAViceCityClone.Shooting;

namespace GTAViceCityClone.Data
{
    /// <summary>
    /// SaveSystem handles binary serialization and deserialization of PlayerData to local disk.
    /// Reconstructed cleanly from Episodes 65, 66.
    /// </summary>
    public static class SaveSystem
    {
        private static readonly string SavePath = Application.persistentDataPath + "/player.sav";

        public static void SavePlayer(PlayerMovement player, PlayerHealth health, GameManager gm, ShootingController shooting)
        {
            BinaryFormatter formatter = new BinaryFormatter();
            FileStream stream = new FileStream(SavePath, FileMode.Create);

            PlayerData data = new PlayerData(player, health, gm, shooting);

            formatter.Serialize(stream, data);
            stream.Close();

            Debug.Log($"Game successfully saved to {SavePath}");
        }

        public static PlayerData LoadPlayer()
        {
            if (File.Exists(SavePath))
            {
                BinaryFormatter formatter = new BinaryFormatter();
                FileStream stream = new FileStream(SavePath, FileMode.Open);

                PlayerData data = formatter.Deserialize(stream) as PlayerData;
                stream.Close();

                Debug.Log($"Game successfully loaded from {SavePath}");
                return data;
            }
            else
            {
                Debug.LogWarning($"Save file not found at {SavePath}");
                return null;
            }
        }

        public static bool HasSaveFile()
        {
            return File.Exists(SavePath);
        }
    }
}
