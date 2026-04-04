using UnityEngine;
using Unity.MLAgents;

namespace SandboxAGI.Scripts
{
    public class PhysicsBreaker : MonoBehaviour
    {
        [Header("Chaos Settings")]
        public float gravityFlipInterval = 60f; // Sekundy między flipami
        public float entropyReversalChance = 0.1f; // Szansa na reverse destruction (per second)
        public float timeReversalDuration = 5f; // Jak długo odtwarzać wstecz

        private float timer;
        private Vector3 originalGravity;
        private bool isReversingTime = false;
        private Vector3[] previousPositions; // Stub dla rewind (rozszerz na rigidbodies)
        private int rewindIndex = 0;

        void Start()
        {
            originalGravity = Physics.gravity;
            timer = Random.Range(0, gravityFlipInterval);
            previousPositions = new Vector3[100]; // Prosty buffer dla pozycji
        }

        void Update()
        {
            if (isReversingTime)
            {
                RewindTime();
                return;
            }

            timer -= Time.deltaTime;
            if (timer <= 0)
            {
                FlipGravity();
                timer = Random.Range(30, gravityFlipInterval * 2); // Dynamiczne interwały
            }

            // Entropy reversal trigger (np. dla rozbitych obiektów – symuluj reverse)
            if (Random.value < entropyReversalChance * Time.deltaTime)
            {
                ReverseEntropy();
            }

            // Zapisz pozycje dla potencjalnego rewind
            SavePosition();
        }

        void FlipGravity()
        {
            Physics.gravity = -Physics.gravity * Random.Range(0.5f, 2f); // Odwróć i skaluj
            Debug.Log($"[ChaosGym] Gravity flipped! New gravity: {Physics.gravity}");
        }

        void ReverseEntropy()
        {
            // Przykładowa implementacja: odwracaj animacje zniszczenia lub particle systems
            // TODO: Integracja z DestructionFX lub custom rigidbody reversal
            foreach (var rb in FindObjectsOfType<Rigidbody>())
            {
                rb.velocity = -rb.velocity * 0.5f; // Odwróć prędkość (efekt "samoistnego składania")
            }
            Debug.Log("[ChaosGym] Entropy reversal triggered – objects reassembling...");
        }

        void TriggerTimeReversal()
        {
            isReversingTime = true;
            rewindIndex = previousPositions.Length - 1;
            Debug.Log("[ChaosGym] Time reversal started – causality inverted!");
            // TODO: Pełny simulation rewind z ML-Agents observations
            Invoke(nameof(EndTimeReversal), timeReversalDuration);
        }

        void RewindTime()
        {
            // Prosty rewind pozycji (dla agenta/obiektów)
            if (rewindIndex >= 0)
            {
                transform.position = previousPositions[rewindIndex];
                rewindIndex--;
            }
        }

        void EndTimeReversal()
        {
            isReversingTime = false;
            Debug.Log("[ChaosGym] Time reversal ended – back to forward causality.");
        }

        void SavePosition()
        {
            // Cykliczny buffer pozycji
            for (int i = 0; i < previousPositions.Length - 1; i++)
            {
                previousPositions[i] = previousPositions[i + 1];
            }
            previousPositions[previousPositions.Length - 1] = transform.position;
        }

        // Public API dla ML-Agents: obserwacje chaosu
        public Vector3 GetCurrentGravity() => Physics.gravity;
        public bool IsChaosActive() => timer < 10f || isReversingTime; // Blisko flipu?
    }
}

// Inspired by Rafał Żabiński’s AGI Testing Ground concept – Dec 10, 2025
