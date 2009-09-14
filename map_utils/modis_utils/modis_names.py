class version(dict):
    def __getitem__(self, vers_string):
        return 'version '+vers_string[1]

class yrng(dict):
    def __getitem__(self, range_string):
        return (2000+int(range_string[0]), 2000+int(range_string[1]))

tfa_chans = ['03','07','08','14','15','37','35','36','38']
lw_chans = ['90']

translations = \
{'channel' : {'03': 'middle infrared', 
            '07': 'daytime land temp', 
            '08': 'nighttime land temp',
            '14': 'ndvi',
            '15': 'evi',
            '35': 'evapotranspiration',
            '36': 'latent heat flux',
            '37': 'potential evapotranspiration',
            '38': 'potential latent heat flux',
            '90': 'land-water'},
'region'  : { 'w': 'world',
            'e': 'europe',
            'f': 'africa',
            'a': 'asia',
            'n': 'north america',
            's': 'south america',
            'o': 'oceania',
            'm': 'mec',
            'i': 'igad',
            'u': 'uk'},
'projection'  : { 's': 'sinusoidal',
                'g': 'geographic'},
'product'  : {'a0': 'mean',
            'a1': 'annual amplitude',
            'a2': 'biannual amplitude',
            'a3': 'triannual amplitude',
            'd1': 'pct variance annual',
            'd2': 'pct variance biannual',
            'd3': 'pct variance triannual',
            'da': 'pct variance cycle',
            'dd': 'unknown',
            'e1': 'pct error input',
            'e2': 'pct error stage 1',
            'e3': 'pct error stage 2',
            'mn': 'minimum',
            'mx': 'maximum',
            'p1': 'annual phase',
            'p2': 'biannual phase',
            'p3': 'triannual phase',
            'vr': 'raw variance',
            'lw': 'land-water',
            'el': 'elevation',
            'sl': 'slope',
            'as': 'aspect',
            'wa': 'water bodies',
            'ma': 'land-water mask'},
'adjustment' : {  '90': 'raw data',
                '91': 'adjustment needed'},
'version' : version(),
'yrng' : yrng()}

def convert(x, channel, product):
    
    if channel is None:
        return x
    
    def get_products(p):
        return map(translations['product'].__getitem__, p)

    def get_channels(c):
        return map(translations['channel'].__getitem__, c)

    if product in get_products(['p1','p2','p3']):
        # Convert phases to units of years
        return (x/100. + 1)/12.

    elif product in get_products(['d1','d2','d3','e1','e2','e3']):
        # Convert percentages to fractions
        return x*100.
        
    else:
        if channel in get_channels(['03']):
            # Convert MIR to reflectance, units???
            return x/10000.

        elif product in get_products(['a0','mn','mx']):

            if channel in get_channels(['07','08']):
                # Convert temperatures to centigrade
                return x/50.+273

            elif channel in get_channels(['14','15']):
                # NDVI and EVI in standard units
                return x/1000.-1
                
            else:
                return x
                
        elif channel in get_channels(['14','15']):
            # NDVI and EVI in standard units
            return x/1000.
            
        elif product in get_products(['a1','a2','a3']):
            # Temperatures in centigrade
            return x/50.
            
        else:
            # Variance of temperature, in centigrade**2
            return x

def parse_one_comp((name, out), comp):
    """
    Reduced over the components to parse the name.
    """
    label = comp[0]
    key = name[:comp[1]]
    newname = name[comp[1]:]
    out[label] = translations[label][key]
    return (newname, out)
            
def parse_filename(name, kind='tfa'):
    """
    Returns the information in the filename as a human-readable dictionary.
    """
    if kind=='tfa':
        comps = [('region',1),('projection',1),('yrng',2),('channel',2),('product',2)]
    elif kind=='lan':
        raise ValueError, 'LAN not supported yet.'
    elif kind=='land-water':
        comps = [('region',1),('projection',1),('version',2),('adjustment',2),('product',2)]
    elif kind=='land-water mask':
        comps = [('region',1),('projection',1),('version',2),('product',2)]
    else:
        raise ValueError, 'Kind must be one of %s, but got %s.'%(['tfa','lan','land-water'], kind)
    
    return reduce(parse_one_comp, comps, (name, {}))[1]