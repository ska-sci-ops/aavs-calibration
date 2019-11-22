import numpy as np
import h5py
import sys
import os

nof_mwa_inputs = 512
nof_mwa_baselines = (nof_mwa_inputs + 1) * nof_mwa_inputs / 2


def get_metadata(datafile, show=True):
    """ Extract metadata from file and perform checks """
    expected_keys = ['n_antennas', 'ts_end', 'n_pols', 'n_beams', 'tile_id', 'n_chans', 'n_samples', 'type',
                     'data_type', 'data_mode', 'ts_start', 'n_baselines', 'n_stokes', 'channel_id', 'timestamp',
                     'date_time', 'n_blocks']

    # Check that keys are present
    if set(expected_keys) - set(datafile.get('root').attrs.keys()) != set():
        raise Exception("Missing metadata in file")

    # All good, get metadata
    metadata = {k: v for (k, v) in datafile.get('root').attrs.items()}
    metadata['nof_integrations'] = metadata['n_blocks'] * metadata['n_samples']

    if show:
        print "---- Meta data ----"
        for k, v in metadata.iteritems():
            if k in ['ts_start', 'nof_integrations', 'channel_id']:
                print "{}:\t{}".format(k, v)
        print '\n'

    return metadata


def generate_indexing_map():
    """ Generate indexing map required by MWA """
    nof_antennas = 256

    # MWA correlator expect antennas in order with interleaved polarisations
    map = np.zeros((nof_mwa_baselines, 2), dtype=np.int)

    # Map to get baseline number for two antennas
    aavs_baseline_number = {}

    counter = 0
    for i in range(nof_antennas):
        for j in range(i, nof_antennas):
            aavs_baseline_number[(i, j)] = counter
            counter += 1

    counter = 0
    for i in range(nof_mwa_inputs):
        for j in range(i, nof_mwa_inputs):
            # Check which polarisations we are talking about, and combine to form pol_index
            i_pol = i % 2
            j_pol = j % 2
            pol_index = i_pol << 1 | j_pol

            # Get corresponding AAVS baseline number
            i_antenna = i / 2
            j_antenna = j / 2
            baseline = aavs_baseline_number[(i_antenna, j_antenna)]

            # Add to mapping
            map[counter] = [baseline, pol_index]

            counter += 1

    return map


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv

    # Script arguments
    parser = OptionParser(usage="usage: %aavs_mwa_corr_converter.py [options]")
    parser.add_option("-f", "--filepath", action="store", dest="filepath", default="",
                      help="Filepath of file to convert [Required]")
    parser.add_option("-o", "--output", action="store", dest="output", default="mwa_compatible_corr.npy",
                      help="Output file [Default: mwa_compatible_corr]")
    parser.add_option("-a", "--average", action="store", dest="n_average", default=1,
                      help="Time samples to average [Default: 1]")
    (conf, args) = parser.parse_args(argv[1:])

    # Check that filepath was provided and that it exists
    if conf.filepath == "" or not (os.path.exists(conf.filepath) and os.path.isfile(conf.filepath)):
        print("Error, valid filepath required!")
        exit()

    n_av = int(conf.n_average)

    # Try to process file
    try:
        # Open HDF5 file
        datafile = h5py.File(conf.filepath, 'r')
        metadata = get_metadata(datafile)
        data = datafile.get('correlation_matrix').get('data')

        # Create output file
        output_autos = open(conf.output + '.LACSPC', 'w')
        output_cross = open(conf.output + '.LCCSPC', 'w')

        # Generate indexing map
        indexing_map = generate_indexing_map()

        # Create converted vis array once
        converted_vis = np.zeros(nof_mwa_baselines, dtype=np.complex64)
        converted_autos = np.zeros(nof_mwa_inputs, dtype=np.float32)
        converted_cross = np.zeros((nof_mwa_inputs - 1) * nof_mwa_inputs / 2, dtype=np.complex64)

        # Process file one integration at a time
        for t in range(metadata['nof_integrations'] / n_av):
            converted_autos.fill(0)
            converted_cross.fill(0)
            for a in range(n_av):
                # Read integration
                vis = data[(t * n_av + a), 0, :, :]

                # Empty converted fill
                converted_vis.fill(0)

                # Correlation matrix is already in upper triangular form, we just need to interleave polarizations
                count_autos = 0
                count_cross = 0
                count_mwabl = 0

                for i in range(nof_mwa_inputs):
                    for j in range(i, nof_mwa_inputs):
                        x, y = indexing_map[count_mwabl]
                        converted_vis[j] = vis[x, y]
                        count_mwabl += 1
                        if i == j and (y == 0 or y == 3):
                            # this is an auto-correlation
                            converted_autos[count_autos] += np.real(converted_vis[j])
                            count_autos += 1
                        else:
                            # this is a cross-correlation
                            converted_cross[count_cross] += converted_vis[j]
                            count_cross += 1
                # Print update
                sys.stdout.write("Processed %d of %d [%.2f%%]      \r" % (t * n_av + a, metadata['nof_integrations'],
                                                                          ((t * n_av + a) / float(
                                                                              metadata['nof_integrations'])) * 100))
                sys.stdout.flush()

            # Correlation matrix interleave, dump to file
            # compute averages, and apply empirical renormalisation for gains
            converted_cross /= (n_av * 100)
            converted_autos /= (n_av * 100)
            converted_cross.tofile(output_cross)
            converted_autos.tofile(output_autos)

    except Exception as e:
        print("Something went wrong: {}".format(e.message))
