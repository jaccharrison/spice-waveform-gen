# (C) Dan White <dan@whiteaudio.com>

import argparse
import os
import re
from decimal import Decimal

# Imports for Python 2 compatibility
from __future__ import print_function, with_statement

# TODO:
# - allow comments in input file
# - passthru (header) comments
# - system info + datetime in output header

def info(s):
    if args.verbose:
        print('INFO:', s)

def error(s):
    print('ERROR:', s)
    sys.exit(1)


def warn(s):
    print('WARNING:', s)





def generate_waveform(d):
    t = Decimal('0.0')

    #first bit interval starts at t=0, start from this value
    lastbit = d[0]
    bitv = Decimal(lastbit) * (bithigh - bitlow) + bitlow
    s = '+ 0 %s' % str(bitv)
    output(s)

    trf = risefall
    tb = bittime - risefall
    t += trf + tb
    for bit in d[1:]:
        # only output a point when there is a change
        if bit != lastbit:
            ti = t + trf
            tf = ti + tb
            lastbitv = Decimal(lastbit) * (bithigh - bitlow) + bitlow
            bitv = Decimal(bit) * (bithigh - bitlow) + bitlow
            output('+ %s %s' % (str(t), str(lastbitv)))
            output('+ %s %s' % (str(ti), str(bitv)))
            #output('+ %s %s' % (str(tf), str(bitv)))

        t += trf + tb
        lastbit = bit



RE_UNIT = re.compile(r'^([0-9e\+\-\.]+)(t|g|meg|x|k|mil|m|u|n|p|f)?')
def unit(s):
    """Takes a string and returns the equivalent float.
    '3.0u' -> 3.0e-6"""
    mult = {'t'  :Decimal('1.0e12'),
            'g'  :Decimal('1.0e9'),
            'meg':Decimal('1.0e6'),
            'x'  :Decimal('1.0e6'),
            'k'  :Decimal('1.0e3'),
            'mil':Decimal('25.4e-6'),
            'm'  :Decimal('1.0e-3'),
            'u'  :Decimal('1.0e-6'),
            'n'  :Decimal('1.0e-9'),
            'p'  :Decimal('1.0e-12'),
            'f'  :Decimal('1.0e-15')}

    m = RE_UNIT.search(s.lower())
    try:
        if m.group(2):
            return Decimal(Decimal(m.group(1)))*mult[m.group(2)]
        else:
            return Decimal(m.group(1))
    except:
        error("Bad unit: %s" % s)




if __name__ == '__main__':
    # python 2 vs 3 compatibility
    try:
        dict.iteritems
    except AttributeError:
        #this is python3
        def iteritems(d):
            return iter(d.items())
    else:
        def iteritems(d):
            return d.iteritems()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description = "Parse a .bus file into a SPICE PWL file")
    parser.add_argument(
        'busfile',
        help = "File with specifying input and clock parameters")
    parser.add_argument(
        'spice',
        choices = ['ngspice', 'ltspice'],
        help = "Informs bus2pwl which PWL specification to follow")
    parser.add_argument(
        '-v', '--verbose',
        help = "Increase output verbosity",
        action = 'store_true')
    parser.add_argument(
        '-o', '--out',
        help = "Name of output PWL file")
    parser.add_argument(
        '-p', '--permissive',
        help = '''If specified, improperly specified bus signal names pass as
        wires instead of triggering errors''',
        action = 'store_true')
    args = parser.parse_args()

    # Basic error checking on input file
    if not args.busfile.endswith('.bus'):
        print("Error: Input file must have '.bus' extension")
        sys.exit(1)

    bus = parse_busfile(args.busfile) # Read and parse input file

    #get the numbers
    risefall = unit(bus['params']['risefall'])
    bittime = unit(bus['params']['bittime'])
    bitlow = unit(bus['params']['bitlow'])
    bithigh = unit(bus['params']['bithigh'])

    #generate output file
    if args.out:
        pwl_name = args.out # if user specified an output file, use it
    else:
        pwl_name = args.busfile.replace('.bus', '.pwl') # default out file name
    with open(pwl_name, 'w') as fpwl:
        output = lambda s: print(s, file=fpwl)
        # output clock definition if specified
        if bus['params']['clockdelay']:
            # calculate clock high time
            if bus['params']['clockrisefall']:
                clockrisefall = unit(bus['params']['clockrisefall'])
            else:
                clockrisefall = risefall

            clockhigh = Decimal('0.5') * (bittime - clockrisefall)
            clockperiod = bittime

            bus['params']['clockrisefall'] = str(clockrisefall)
            bus['params']['clockhigh'] = str(clockhigh)
            bus['params']['clockperiod'] = str(clockperiod)

            clk = 'Vclock clock 0 pulse(%(bitlow)s %(bithigh)s %(clockdelay)s %(clockrisefall)s %(clockrisefall)s %(clockhigh)s %(clockperiod)s)' % bus['params']
            info(clk)

            output(clk)
            output('')

        #output each input source
        for name, signal in iteritems(bus['signals']):
            #first line
            s = 'V%s %s 0 PWL' % (name, name)
            info(s)
            output(s)

            generate_waveform(signal)
            output('')

        info('Output file: ' + pwl_name)