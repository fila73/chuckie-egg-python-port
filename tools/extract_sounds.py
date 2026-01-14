"""
Chuckie Egg Sound & Music Tool
Extracts and converts ZX Spectrum beeper note data to WAV audio.

Note data format: pairs of (duration, pitch_index)
- Duration: number of "beats"
- Pitch: index into frequency table (higher = higher pitch)
"""

import wave
import struct
import math
import os

# Frequencies for semitones
# We'll use Middle C (C4) as index 0x10 ($16)
def pitch_to_frequency(pitch_index):
    """
    Convert pitch index from assembly to frequency in Hz.
    Note data from Chuckie Egg: higher index = higher pitch.
    """
    if pitch_index == 0:
        return 0
        
    # Standard Pitch (A4 = 440Hz)
    # If 0x10 is C4 (261.63 Hz)
    # A4 (440Hz) is 9 semitones above C4.
    # So index for A4 would be 0x10 + 9 = 0x19
    
    # Let's define C4 at 0x10
    base_freq = 261.63 # C4
    semitone_offset = pitch_index - 0x10
    
    # Formula: freq = base * 2^(semitones/12)
    freq = base_freq * (2 ** (semitone_offset / 12.0))
    return freq

def generate_square_wave(frequency, duration_ms, sample_rate=44100):
    """Generate a square wave (classic Spectrum beeper sound)."""
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    
    if frequency <= 0:
        return [0] * num_samples
    
    period = sample_rate / frequency
    
    for i in range(num_samples):
        if (i % period) < (period / 2):
            samples.append(16000)  # High
        else:
            samples.append(-16000)  # Low
    
    return samples

def save_wav(output_path, note_data, tempo_ms=150):
    """Generate WAV file from note data."""
    sample_rate = 44100
    all_samples = []
    
    for duration, pitch in note_data:
        freq = pitch_to_frequency(pitch)
        note_duration = duration * tempo_ms
        
        samples = generate_square_wave(freq, note_duration, sample_rate)
        all_samples.extend(samples)
        
        # Small gap between notes (authentic beeper style)
        gap_samples = int(sample_rate * 0.01) # 10ms gap
        all_samples.extend([0] * gap_samples)
    
    # Write WAV file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for s in all_samples:
            wav_file.writeframes(struct.pack('<h', int(s)))
    
    print(f"Generated: {os.path.basename(output_path)} ({len(all_samples)/sample_rate:.2f}s)")

# --- MELODY DATA ---

# Theme tune data extracted from chuckie-egg.skool ($ae0c - $ae68)
THEME_TUNE = [
    (0x01, 0x10), (0x01, 0x10), (0x01, 0x12), (0x01, 0x12),
    (0x01, 0x0d), (0x01, 0x0d), (0x02, 0x10), (0x01, 0x10),
    (0x01, 0x10), (0x01, 0x12), (0x01, 0x12), (0x01, 0x0d),
    (0x01, 0x0d), (0x02, 0x10), (0x01, 0x10), (0x01, 0x10),
    (0x02, 0x12), (0x02, 0x15), (0x02, 0x14), (0x02, 0x14),
    (0x02, 0x12), (0x02, 0x10), (0x02, 0x0e), (0x01, 0x0e),
    (0x01, 0x0e), (0x01, 0x10), (0x01, 0x10), (0x01, 0x0b),
    (0x01, 0x0b), (0x02, 0x0e), (0x01, 0x0e), (0x01, 0x0e),
    (0x01, 0x10), (0x01, 0x10), (0x01, 0x0b), (0x01, 0x0b),
    (0x02, 0x0e), (0x01, 0x0e), (0x01, 0x0e), (0x02, 0x10),
    (0x02, 0x12), (0x02, 0x13), (0x02, 0x10), (0x02, 0x0e),
    (0x02, 0x0b), (0x02, 0x07)
]

# Death tune data extracted from chuckie-egg.skool ($ae6a - $ae9a)
DEATH_TUNE = [
    (0x02, 0x08), (0x02, 0x08), (0x02, 0x08), (0x02, 0x08),
    (0x02, 0x06), (0x02, 0x04), (0x02, 0x04), (0x02, 0x03),
    (0x02, 0x01), (0x02, 0x01),  # First 10 notes (verified OK)
    (0x02, 0x04), (0x02, 0x08), (0x02, 0x0d), (0x02, 0x0d),
    (0x02, 0x0d), (0x02, 0x0d), (0x02, 0x0b), (0x02, 0x09),
    (0x02, 0x09), (0x02, 0x08), (0x02, 0x06), (0x02, 0x06),
    (0x02, 0x08), (0x02, 0x09)
]

if __name__ == "__main__":
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "sounds")
    
    # Theme Tune (Fast/Classic tempo)
    save_wav(os.path.join(assets_dir, "theme_tune.wav"), THEME_TUNE, tempo_ms=130)
    
    # Death Tune (Slower)
    save_wav(os.path.join(assets_dir, "death_tune.wav"), DEATH_TUNE, tempo_ms=200)

    # --- SFX GENERATION ---
    sample_rate = 44100

    def generate_sfx(filename, samples):
        path = os.path.join(assets_dir, filename)
        with wave.open(path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for s in samples:
                wav_file.writeframes(struct.pack('<h', int(s)))
        print(f"Generated SFX: {filename}")

    # Spectrum beeper timing approx: 
    # freq = CPU_CLOCK / (2 * cycles_per_toggle * H)
    def h_to_freq(h):
        if h <= 0: return 0
        return 3500000 / (2 * 50 * h) # 50 is approx T-states per toggle loop

    # 1. Walk SFX (H=40, L=5)
    walk_freq = h_to_freq(40)
    walk_samples = generate_square_wave(walk_freq, 10, sample_rate) # 10ms blip
    generate_sfx("sfx_walk.wav", walk_samples)

    # 2. Climb SFX (H=30, L=20)
    climb_freq = h_to_freq(30)
    climb_samples = generate_square_wave(climb_freq, 30, sample_rate) # 30ms blip
    generate_sfx("sfx_climb.wav", climb_samples)

    # 3. Collection SFX (Chirp: H rises as timer falls)
    # H = (0..31) + 6
    collect_samples = []
    for timer in range(31, -1, -1):
        h = timer + 6
        freq = h_to_freq(h)
        # L=2 pulses
        duration_ms = (2 / freq) * 1000 if freq > 0 else 0
        collect_samples.extend(generate_square_wave(freq, duration_ms, sample_rate))
        # Wait 4 frames (approx 80ms)
        collect_samples.extend([0] * int(sample_rate * 0.08)) 
    generate_sfx("sfx_collect.wav", collect_samples)

    # 4. Jump SFX (Rising "boing")
    jump_samples = []
    for h in range(40, 10, -2):
        freq = h_to_freq(h)
        jump_samples.extend(generate_square_wave(freq, 10, sample_rate))
    generate_sfx("sfx_jump.wav", jump_samples)

    print("\nSound extraction complete!")
