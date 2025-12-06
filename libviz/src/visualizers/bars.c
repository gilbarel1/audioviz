/**
 * Frequency Bars Visualizer
 * 
 * Maps FFT bins to logarithmically-scaled vertical bars.
 */

#include "bars.h"
#include <math.h>
#include <string.h>
#include <stdio.h>

#define NUM_BARS 32
#define DECAY_RATE 0.95f
#define SMOOTHING_ALPHA 0.3f

struct BarsVisualizer {
    int num_bars;
    float bar_heights[NUM_BARS];
    float bar_peaks[NUM_BARS];
};

BarsVisualizer* bars_visualizer_create() {
    BarsVisualizer* viz = calloc(1, sizeof(BarsVisualizer));
    if (!viz) {
        return NULL;
    }
    
    viz->num_bars = NUM_BARS;
    memset(viz->bar_heights, 0, sizeof(viz->bar_heights));
    memset(viz->bar_peaks, 0, sizeof(viz->bar_peaks));
    
    return viz;
}

void bars_visualizer_update(BarsVisualizer* viz, const float* magnitude, int bin_count) {
    if (!viz || !magnitude) {
        return;
    }
    
    // Map FFT bins to bars using logarithmic scaling
    for (int i = 0; i < viz->num_bars; i++) {
        // Calculate frequency range for this bar (logarithmic)
        float freq_start = powf(2.0f, (float)i / viz->num_bars * 10.0f);
        float freq_end = powf(2.0f, (float)(i + 1) / viz->num_bars * 10.0f);
        
        // Map to bin indices
        int bin_start = (int)(freq_start * bin_count / 1024.0f);
        int bin_end = (int)(freq_end * bin_count / 1024.0f);
        
        if (bin_start >= bin_count) bin_start = bin_count - 1;
        if (bin_end >= bin_count) bin_end = bin_count - 1;
        if (bin_end <= bin_start) bin_end = bin_start + 1;
        
        // Average magnitude across bin range
        float sum = 0.0f;
        for (int j = bin_start; j < bin_end; j++) {
            sum += magnitude[j];
        }
        float avg = sum / (bin_end - bin_start);
        
        // Apply smoothing
        float new_height = SMOOTHING_ALPHA * avg + (1.0f - SMOOTHING_ALPHA) * viz->bar_heights[i];
        
        // Apply decay to previous height
        viz->bar_heights[i] = fmaxf(new_height, viz->bar_heights[i] * DECAY_RATE);
        
        // Update peak
        if (viz->bar_heights[i] > viz->bar_peaks[i]) {
            viz->bar_peaks[i] = viz->bar_heights[i];
        } else {
            viz->bar_peaks[i] *= 0.99f;  // Slower decay for peaks
        }
    }
}

void bars_visualizer_get_bars(const BarsVisualizer* viz, float* heights, float* peaks) {
    if (!viz) {
        return;
    }
    
    if (heights) {
        memcpy(heights, viz->bar_heights, viz->num_bars * sizeof(float));
    }
    
    if (peaks) {
        memcpy(peaks, viz->bar_peaks, viz->num_bars * sizeof(float));
    }
}

int bars_visualizer_get_num_bars(const BarsVisualizer* viz) {
    return viz ? viz->num_bars : 0;
}

void bars_visualizer_destroy(BarsVisualizer* viz) {
    free(viz);
}
