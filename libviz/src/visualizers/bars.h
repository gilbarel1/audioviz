/**
 * Frequency Bars Visualizer Interface
 */

#ifndef BARS_H
#define BARS_H

#include <stdlib.h>

typedef struct BarsVisualizer BarsVisualizer;

/**
 * Create bars visualizer.
 */
BarsVisualizer* bars_visualizer_create();

/**
 * Update bars with new FFT data.
 * 
 * @param viz Visualizer instance
 * @param magnitude FFT magnitude bins
 * @param bin_count Number of bins
 */
void bars_visualizer_update(BarsVisualizer* viz, const float* magnitude, int bin_count);

/**
 * Get bar heights and peaks.
 * 
 * @param viz Visualizer instance
 * @param heights Output array for bar heights (can be NULL)
 * @param peaks Output array for bar peaks (can be NULL)
 */
void bars_visualizer_get_bars(const BarsVisualizer* viz, float* heights, float* peaks);

/**
 * Get number of bars.
 */
int bars_visualizer_get_num_bars(const BarsVisualizer* viz);

/**
 * Destroy visualizer.
 */
void bars_visualizer_destroy(BarsVisualizer* viz);

#endif // BARS_H
