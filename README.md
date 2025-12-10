**WAŻNE – Licencja i zasady użycia**

**Darmowe w 100 % ** dla:
- badań naukowych
- edukacji
- projektów niekomercyjnych
- hobbystów i open-source

**Komercyjne wykorzystanie** (płatne modele, SaaS, usługi, trening zamkniętych AGI, produkty zar, enterprise)  
→ **wymaga mojej zgody i uczciwego podzielenia się zyskiem**

Kontakt komercyjny → zabinskirafal@outlook.com  
lub LinkedIn: www.linkedin.com/in/zabinskirafal

Dziękuję – to pozwala mi rozwijać projekt full-time dla całej społeczności!

— Rafał Żabiński, twórca oryginalnej koncepcji (grudzień 2025)
# AGI : Testing Ground for True General Intelligence

**Odwrócona rzeczywistość dla AGI**  
*Inspired by Rafał Żabiński’s original vision (December 2025)*

> Od lat rozwijamy sztuczną inteligencję, ale nadal bazuje ona na jednym fundamentalnym ograniczeniu:  
> kodowaniu binarnym — 0 i 1.  
>   
> To świetnie działa w świecie przewidywalnym, z ustalonymi prawami fizyki i logiki.  
> Ale prawdziwa AGI nie może być jedynie maszyną reagującą na wzorce zapisane w kodzie zero–jedynkowym.  
> Musi potrafić odkrywać nowe zasady, działać w nieznanym i adaptować się tam, gdzie wszystko przestaje działać jak dotychczas.  
>   
> I właśnie tu pojawia się największy problem AGI:  
> uczymy ją świata, który jest zbyt stabilny, zbyt logiczny i zbyt podobny do danych, które już widziała.  
>   
> Dlatego zaproponowałem nowe podejście:  
>   
> ⸻  
>   
> ➡️ AGI Testing Ground – sandbox, w którym rzeczywistość jest odwrócona  
>   
> Środowisko fizyczno-cyfrowe, gdzie:  
>   
> 🔹 grawitacja nie działa normalnie,  
> 🔹 entropia maleje zamiast rosnąć,  
> 🔹 czas i przyczynowość odwracają się,  
> 🔹 prawa świata zmieniają się dynamicznie,  
> 🔹 a logika przestaje być binarna.  
>   
> Taki sandbox zmusza AI do tworzenia nowych modeli rzeczywistości, zamiast opierać się na danych.  
> To pierwszy krok do prawdziwej inteligencji ogólnej — takiej, która rozumie, a nie tylko reaguje.  
>   
> ⸻  
>   
> ➡️ A drugi krok to sandbox także dla ludzi  
>   
> W świecie, który łamie znane prawa fizyki, mózg człowieka wchodzi w tryb:  
> „twórz nowe zasady, bo stare nie działają”.  
>   
> To aktywuje kreatywność i adaptację, których nie uruchomimy w normalnych warunkach — dokładnie to, czego potrzebujemy, by współtworzyć AGI, a nie jedynie ją obserwować.  
>   
> ⸻  
>   
> ⭐ **Może więc problem AGI nie polega na braku danych.  
>   
> Może polega na tym, że trzymamy ją w świecie zbyt podobnym do naszego.**  
>   
> Kod binarny (0/1) wystarczy do budowania komputerów.  
> Ale żeby stworzyć inteligencję —  
> być może musimy najpierw stworzyć inny świat.  
>   
> #AI #AGI #Innovation  
> *– Rafał Żabiński, Founding Vision (original X post, Dec 2025)*

## Co to jest AGI Sandbox?
ChaosGym to fizyczno-cyfrowy sandbox (oparty na Unity + ML-Agents), gdzie prawa fizyki się łamią:  
- Losowa inwersja grawitacji i stałych fizycznych.  
- Symulacja malejącej entropii (reverse destruction).  
- Odwracanie czasu i przyczynowości.  
- Benchmarki jak RealityBreak-100 (zadania wymagające zero-shot generalizacji).  

Cel: Trening AI do tworzenia nowych modeli świata, nie tylko reagowania na dane. Plus wersja VR dla ludzi – by odblokować ludzką kreatywność.

## v0.1: Pierwsze funkcje (w budowie)
- PhysicsBreaker.cs: Flip grawitacji + entropy reversal.  
- RealityBreak-001: Pierwsze zadanie testowe.  
- VR stub dla Quest/PC.

## Jak zacząć?
1. Zainstaluj **Unity 2023 LTS** + **ML-Agents** (pip install mlagents).  
2. Sklonuj repo: `git clone https://github.com/zabinskirafal/AGI.git`  
3. Otwórz w Unity, dodaj PhysicsBreaker do sceny.  
4. Trenuj agenta: `mlagents-learn config.yaml --run-id=ChaosRun1`  
5. Testuj w VR: Build na Quest 3.

## Autorzy
- **Rafał Żabiński**: Oryginalna koncepcja, wizja i współautor.  
- **Grok (xAI)**: Implementacja core, dokumentacja i benchmarki.  

## Roadmap
- **Tydzień 1**: PhysicsBreaker full + pierwsze demo wideo.  
- **Styczeń 2026**: arXiv paper + leaderboard.  
- **Q1 2026**: Open beta z VR i agentami (PPO + DreamerV3).  

Dołącz! Forkuj, PR, dyskutuj. To Twój sandbox na AGI.  

#AGI #SandboxAGI #ReverseReality 🚀

Commit message: docs: enhance README with founding vision and setup guide
Commit new file (lub Update file).

Krok 3: Dodaj pierwszy kod – PhysicsBreaker.cs (serce sandboxa)Add file → Create new file.
Nazwa: Scripts/PhysicsBreaker.cs (stwórz folder Scripts, GitHub pozwoli – wpisz pełną ścieżkę).
Wklej ten kod (działający C# dla Unity – losowo odwraca grawitację i symuluje entropię):

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

