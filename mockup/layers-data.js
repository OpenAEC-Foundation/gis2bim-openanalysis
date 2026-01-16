// GIS2BIM OpenAnalysis - Available Layers Database
// Based on PDOK and other Dutch geodata services

const AVAILABLE_LAYERS = [
    // === TOPOGRAFIE ===
    {
        id: 'top10nl',
        name: 'TOP10NL Topografische Kaart',
        description: 'Topografische basiskaart van Nederland 1:10.000',
        category: 'topografie',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0',
        layer: 'standaard',
        color: '#10b981',
        default: true
    },
    {
        id: 'top25raster',
        name: 'TOP25 Raster',
        description: 'Topografische kaart 1:25.000',
        category: 'topografie',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/kadaster/top25raster/wmts/v1_0',
        layer: 'top25raster',
        color: '#059669'
    },
    {
        id: 'top50raster',
        name: 'TOP50 Raster',
        description: 'Topografische kaart 1:50.000',
        category: 'topografie',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/kadaster/top50raster/wmts/v1_0',
        layer: 'top50raster',
        color: '#047857'
    },
    {
        id: 'top100raster',
        name: 'TOP100 Raster',
        description: 'Topografische kaart 1:100.000',
        category: 'topografie',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/kadaster/top100raster/wmts/v1_0',
        layer: 'top100raster',
        color: '#065f46'
    },
    {
        id: 'brt-grijs',
        name: 'BRT Achtergrondkaart Grijs',
        description: 'Grijze topografische achtergrondkaart',
        category: 'topografie',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0',
        layer: 'grijs',
        color: '#6b7280'
    },
    {
        id: 'brt-pastel',
        name: 'BRT Achtergrondkaart Pastel',
        description: 'Pastel topografische achtergrondkaart',
        category: 'topografie',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0',
        layer: 'pastel',
        color: '#f472b6'
    },
    {
        id: 'opentopo',
        name: 'OpenTopo',
        description: 'Open topografische kaart Nederland',
        category: 'topografie',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/kadaster/opentopo/wmts/v1_0',
        layer: 'opentopoachtergrondkaart',
        color: '#22c55e'
    },
    {
        id: 'openstreetmap',
        name: 'OpenStreetMap',
        description: 'OpenStreetMap - open source kaart van de wereld',
        category: 'topografie',
        source: 'OSM',
        type: 'TILE',
        url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        layer: 'osm',
        color: '#0ea5e9',
        default: false
    },

    // === KADASTER ===
    {
        id: 'kadastrale-kaart',
        name: 'Kadastrale Kaart',
        description: 'Kadastrale percelen en grenzen',
        category: 'kadaster',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0',
        layer: 'Perceel',
        color: '#dc2626',
        default: true
    },
    {
        id: 'bag-panden',
        name: 'BAG Panden',
        description: 'Basisregistratie Adressen en Gebouwen - Panden',
        category: 'kadaster',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/lv/bag/wms/v2_0',
        layer: 'pand',
        color: '#ef4444',
        default: true
    },
    {
        id: 'bag-panden-compleet',
        name: 'BAG Panden + Kadaster + Straatnamen',
        description: 'BAG Panden met kadastrale lijnen (punt-streep) en straatnamen',
        category: 'kadaster',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/lv/bag/wms/v2_0',
        layer: 'pand',
        overlayLayers: ['kadastrale-grenslijn', 'straatnamen'],
        color: '#ef4444',
        default: false
    },
    {
        id: 'kadastrale-grenslijn',
        name: 'Kadastrale Grenslijn (punt-streep)',
        description: 'Kadastrale perceelgrenzen als punt-streep lijn',
        category: 'kadaster',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0',
        layer: 'KastersGrenslijn',
        style: 'kadastralegrenslijn',
        color: '#b91c1c',
        default: false
    },
    {
        id: 'straatnamen',
        name: 'Straatnamen',
        description: 'Openbare ruimte namen (straten, pleinen)',
        category: 'kadaster',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0',
        layer: 'OpenbareRuimteNaam',
        color: '#7f1d1d',
        default: false
    },
    {
        id: 'bag-verblijfsobjecten',
        name: 'BAG Verblijfsobjecten',
        description: 'BAG Verblijfsobjecten met adressen',
        category: 'kadaster',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/lv/bag/wms/v2_0',
        layer: 'verblijfsobject',
        color: '#f87171'
    },
    {
        id: 'brk-percelen',
        name: 'BRK Kadastrale Percelen',
        description: 'Basisregistratie Kadaster percelen',
        category: 'kadaster',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/kadaster/kadastralekaart/wms/v5_0',
        layer: 'Perceel',
        color: '#b91c1c'
    },

    // === BGT ===
    {
        id: 'bgt-standaard',
        name: 'BGT Standaard',
        description: 'Basisregistratie Grootschalige Topografie',
        category: 'topografie',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/lv/bgt/wmts/v1_0',
        layer: 'standaardvisualisatie',
        color: '#8b5cf6',
        default: true
    },
    {
        id: 'bgt-lijngericht',
        name: 'BGT Lijngericht',
        description: 'BGT Lijngerichte visualisatie',
        category: 'topografie',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/lv/bgt/wmts/v1_0',
        layer: 'lijngerichte_visualisatie',
        color: '#7c3aed'
    },
    {
        id: 'bgt-omtrekgericht',
        name: 'BGT Omtrekgericht',
        description: 'BGT Omtrekgerichte visualisatie',
        category: 'topografie',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/lv/bgt/wmts/v1_0',
        layer: 'omtrekgerichte_visualisatie',
        color: '#6d28d9'
    },

    // === LUCHTFOTO'S ===
    {
        id: 'luchtfoto-actueel',
        name: 'Luchtfoto Actueel',
        description: 'Meest recente luchtfoto (PDOK)',
        category: 'luchtfoto',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0',
        layer: 'Actueel_orthoHR',
        color: '#14b8a6',
        default: true
    },
    {
        id: 'luchtfoto-2023',
        name: 'Luchtfoto 2023',
        description: 'Luchtfoto opname 2023',
        category: 'luchtfoto',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0',
        layer: '2023_orthoHR',
        color: '#0d9488'
    },
    {
        id: 'luchtfoto-2022',
        name: 'Luchtfoto 2022',
        description: 'Luchtfoto opname 2022',
        category: 'luchtfoto',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0',
        layer: '2022_orthoHR',
        color: '#0f766e'
    },
    {
        id: 'luchtfoto-2021',
        name: 'Luchtfoto 2021',
        description: 'Luchtfoto opname 2021',
        category: 'luchtfoto',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0',
        layer: '2021_orthoHR',
        color: '#115e59'
    },
    {
        id: 'luchtfoto-infrarood',
        name: 'Luchtfoto Infrarood',
        description: 'Infrarood luchtfoto voor vegetatie analyse',
        category: 'luchtfoto',
        source: 'PDOK',
        type: 'WMTS',
        url: 'https://service.pdok.nl/hwh/luchtfotocir/wmts/v1_0',
        layer: 'Actueel_ortho25IR',
        color: '#be123c'
    },

    // === HOOGTE (AHN) ===
    {
        id: 'ahn4-dsm',
        name: 'AHN4 Hoogtekaart (DSM)',
        description: 'Actueel Hoogtebestand NL 4 - Digital Surface Model',
        category: 'milieu',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/rws/ahn/wms/v1_0',
        layer: 'dsm_05m',
        color: '#6366f1',
        default: true
    },
    {
        id: 'ahn4-dtm',
        name: 'AHN4 Maaiveldhoogte (DTM)',
        description: 'Actueel Hoogtebestand NL 4 - Digital Terrain Model',
        category: 'milieu',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/rws/ahn/wms/v1_0',
        layer: 'dtm_05m',
        color: '#4f46e5'
    },
    {
        id: 'ahn3-dsm',
        name: 'AHN3 Hoogtekaart (DSM)',
        description: 'Actueel Hoogtebestand NL 3 - Digital Surface Model',
        category: 'milieu',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/rws/ahn/wms/v1_0',
        layer: 'ahn3_05m_dsm',
        color: '#4338ca'
    },

    // === MILIEU ===
    {
        id: 'geluid-weg',
        name: 'Geluidskaart Wegverkeer',
        description: 'Geluidsbelasting door wegverkeer (Lden)',
        category: 'milieu',
        source: 'RIVM',
        type: 'WMS',
        url: 'https://geodata.rivm.nl/geoserver/wms',
        layer: 'ggk:ggk_lden_weg',
        color: '#06b6d4',
        default: true
    },
    {
        id: 'geluid-rail',
        name: 'Geluidskaart Railverkeer',
        description: 'Geluidsbelasting door railverkeer',
        category: 'milieu',
        source: 'RIVM',
        type: 'WMS',
        url: 'https://geodata.rivm.nl/geoserver/wms',
        layer: 'ggk:ggk_lden_rail',
        color: '#0891b2'
    },
    {
        id: 'geluid-industrie',
        name: 'Geluidskaart Industrie',
        description: 'Geluidsbelasting door industrie',
        category: 'milieu',
        source: 'RIVM',
        type: 'WMS',
        url: 'https://geodata.rivm.nl/geoserver/wms',
        layer: 'ggk:ggk_lden_industrie',
        color: '#0e7490'
    },
    {
        id: 'geluid-luchtvaart',
        name: 'Geluidskaart Luchtvaart',
        description: 'Geluidsbelasting door luchtvaart',
        category: 'milieu',
        source: 'RIVM',
        type: 'WMS',
        url: 'https://geodata.rivm.nl/geoserver/wms',
        layer: 'ggk:ggk_lden_luchtvaart',
        color: '#155e75'
    },
    {
        id: 'bodemkaart',
        name: 'Bodemkaart',
        description: 'Bodemtypen en grondsoorten 1:50.000',
        category: 'milieu',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/bzk/bro-bodemkaart/wms/v1_0',
        layer: 'bodemkaart',
        color: '#ca8a04',
        default: true
    },
    {
        id: 'grondwatertrappen',
        name: 'Grondwatertrappen',
        description: 'Grondwaterstand indicatie',
        category: 'milieu',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/bzk/bro-bodemkaart/wms/v1_0',
        layer: 'grondwatertrappen',
        color: '#a16207'
    },

    // === NATUUR & ECOLOGIE ===
    {
        id: 'natura2000',
        name: 'Natura 2000 Gebieden',
        description: 'Europese beschermde natuurgebieden',
        category: 'milieu',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/rvo/natura2000/wms/v1_0',
        layer: 'natura2000',
        color: '#22c55e',
        default: true
    },
    {
        id: 'nnn',
        name: 'Natuurnetwerk Nederland',
        description: 'NNN / Ecologische Hoofdstructuur',
        category: 'milieu',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/rvo/nnn/wms/v1_0',
        layer: 'nnn',
        color: '#16a34a'
    },
    {
        id: 'stiltegebieden',
        name: 'Stiltegebieden',
        description: 'Provinciale stiltegebieden',
        category: 'milieu',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/provincies/stiltegebieden/wms/v1_0',
        layer: 'stiltegebieden',
        color: '#15803d'
    },

    // === RUIMTELIJKE PLANNEN ===
    {
        id: 'bestemmingsplan',
        name: 'Bestemmingsplannen',
        description: 'Geldende bestemmingsplannen',
        category: 'thematisch',
        source: 'Ruimtelijkeplannen.nl',
        type: 'WMS',
        url: 'https://service.pdok.nl/pbl/ruimtelijkeplannen/wms/v1_0',
        layer: 'bestemmingsplangebied',
        color: '#f97316',
        default: true
    },
    {
        id: 'enkelbestemming',
        name: 'Enkelbestemmingen',
        description: 'Bestemmingsplan enkelbestemmingen',
        category: 'thematisch',
        source: 'Ruimtelijkeplannen.nl',
        type: 'WMS',
        url: 'https://service.pdok.nl/pbl/ruimtelijkeplannen/wms/v1_0',
        layer: 'enkelbestemming',
        color: '#ea580c'
    },
    {
        id: 'dubbelbestemming',
        name: 'Dubbelbestemmingen',
        description: 'Bestemmingsplan dubbelbestemmingen',
        category: 'thematisch',
        source: 'Ruimtelijkeplannen.nl',
        type: 'WMS',
        url: 'https://service.pdok.nl/pbl/ruimtelijkeplannen/wms/v1_0',
        layer: 'dubbelbestemming',
        color: '#c2410c'
    },

    // === CULTUREEL ERFGOED ===
    {
        id: 'rijksmonumenten',
        name: 'Rijksmonumenten',
        description: 'Beschermde rijksmonumenten',
        category: 'thematisch',
        source: 'RCE',
        type: 'WMS',
        url: 'https://services.rce.geovoorziening.nl/rce/wms',
        layer: 'rijksmonumenten_punt',
        color: '#ec4899',
        default: true
    },
    {
        id: 'beschermde-gezichten',
        name: 'Beschermde Stads- en Dorpsgezichten',
        description: 'Rijksbeschermde stads- en dorpsgezichten',
        category: 'thematisch',
        source: 'RCE',
        type: 'WMS',
        url: 'https://services.rce.geovoorziening.nl/rce/wms',
        layer: 'beschermde_gezichten',
        color: '#db2777'
    },
    {
        id: 'archeologische-monumenten',
        name: 'Archeologische Monumenten',
        description: 'Rijksmonumenten archeologie',
        category: 'thematisch',
        source: 'RCE',
        type: 'WMS',
        url: 'https://services.rce.geovoorziening.nl/rce/wms',
        layer: 'archeologische_monumenten',
        color: '#be185d'
    },

    // === WATER ===
    {
        id: 'waterschappen',
        name: 'Waterschapsgrenzen',
        description: 'Grenzen van waterschappen',
        category: 'infrastructuur',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/kadaster/bestuurlijkegebieden/wms/v1_0',
        layer: 'Waterschapsgebied',
        color: '#3b82f6',
        default: true
    },
    {
        id: 'overstromingsrisico',
        name: 'Overstromingsrisico',
        description: 'Risico op overstroming bij dijkdoorbraak',
        category: 'milieu',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/rws/overstromingsrisico/wms/v1_0',
        layer: 'maximale_waterdiepte',
        color: '#1d4ed8'
    },
    {
        id: 'legger-watergangen',
        name: 'Watergangen',
        description: 'Legger watergangen en kunstwerken',
        category: 'infrastructuur',
        source: 'Waterschappen',
        type: 'WMS',
        url: 'https://service.pdok.nl/hwh/legger/wms/v1_0',
        layer: 'primaire_watergang',
        color: '#2563eb'
    },

    // === INFRASTRUCTUUR ===
    {
        id: 'nwb-wegen',
        name: 'NWB Wegennetwerk',
        description: 'Nationaal Wegenbestand',
        category: 'infrastructuur',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/rws/nwbwegen/wms/v1_0',
        layer: 'wegvakken',
        color: '#64748b'
    },
    {
        id: 'spoorwegen',
        name: 'Spoorwegen',
        description: 'Spoorwegennetwerk Nederland',
        category: 'infrastructuur',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/prorail/spoorwegen/wms/v1_0',
        layer: 'spooras',
        color: '#475569'
    },
    {
        id: 'hoogspanning',
        name: 'Hoogspanningslijnen',
        description: 'Bovengrondse hoogspanningslijnen',
        category: 'infrastructuur',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/rvo/hoogspanningslijnen/wms/v1_0',
        layer: 'hoogspanningslijnen',
        color: '#fbbf24'
    },
    {
        id: 'windturbines',
        name: 'Windturbines',
        description: 'Locaties van windturbines',
        category: 'infrastructuur',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/rvo/windturbines/wms/v1_0',
        layer: 'windturbine',
        color: '#94a3b8'
    },

    // === ENERGIE ===
    {
        id: 'energielabels',
        name: 'Energielabels',
        description: 'Energielabels van gebouwen',
        category: 'thematisch',
        source: 'EP-Online',
        type: 'WMS',
        url: 'https://service.pdok.nl/rvo/energielabel/wms/v1_0',
        layer: 'energielabel',
        color: '#f97316',
        default: true
    },
    {
        id: 'warmtenetten',
        name: 'Warmtenetten',
        description: 'Bestaande warmtenetten',
        category: 'infrastructuur',
        source: 'PDOK',
        type: 'WMS',
        url: 'https://service.pdok.nl/rvo/warmtenetten/wms/v1_0',
        layer: 'warmtenet',
        color: '#ea580c'
    },

    // === STATISTIEK ===
    {
        id: 'cbs-wijken-buurten',
        name: 'CBS Wijken en Buurten',
        description: 'Statistische gebiedsindeling',
        category: 'thematisch',
        source: 'CBS',
        type: 'WMS',
        url: 'https://service.pdok.nl/cbs/wijkenbuurten/wms/v1_0',
        layer: 'buurten',
        color: '#a78bfa',
        default: true
    },
    {
        id: 'cbs-gemeenten',
        name: 'CBS Gemeentegrenzen',
        description: 'Gemeentegrenzen Nederland',
        category: 'thematisch',
        source: 'CBS',
        type: 'WMS',
        url: 'https://service.pdok.nl/kadaster/bestuurlijkegebieden/wms/v1_0',
        layer: 'Gemeentegebied',
        color: '#8b5cf6'
    },
    {
        id: 'cbs-provincies',
        name: 'CBS Provinciegrenzen',
        description: 'Provinciegrenzen Nederland',
        category: 'thematisch',
        source: 'CBS',
        type: 'WMS',
        url: 'https://service.pdok.nl/kadaster/bestuurlijkegebieden/wms/v1_0',
        layer: 'Provinciegebied',
        color: '#7c3aed'
    },

    // === KABELS & LEIDINGEN ===
    {
        id: 'klic-overzicht',
        name: 'KLIC Netbeheerders',
        description: 'Overzicht netbeheerders (indicatief)',
        category: 'infrastructuur',
        source: 'KLIC',
        type: 'WMS',
        url: 'https://service.pdok.nl/kadaster/klic/wms/v1_0',
        layer: 'netbeheerders',
        color: '#64748b',
        default: true
    },

    // === SAMENVATTING ===
    {
        id: 'samenvatting',
        name: 'Samenvatting & Overzicht',
        description: 'Locatiegegevens en bronvermelding',
        category: 'thematisch',
        source: 'Generated',
        type: 'summary',
        color: '#334155',
        default: true
    }
];

// Default layer configuration
const DEFAULT_LAYERS = AVAILABLE_LAYERS.filter(l => l.default).map(l => l.id);

// Standard Report Configuration - 12 pages with working layers
// All layer IDs must match backend map_service.py LAYERS dict
const STANDARD_REPORT = {
    name: 'Standaard Locatie Rapport',
    description: 'Compleet overzicht van een locatie met alle relevante geodata',
    pages: [
        // 1. TOP10NL Topografische Kaart
        {
            id: 'page-top10nl',
            layerId: 'top10nl',
            title: 'Topografische Kaart',
            subtitle: 'TOP10NL Basiskaart',
            scale: 2500,
            description: 'Overzicht van de locatie op topografische ondergrond'
        },
        // 2. Kadastrale Kaart + BAG op Luchtfoto
        {
            id: 'page-kadaster-luchtfoto',
            layerId: 'luchtfoto-actueel',
            overlayLayers: ['kadastrale-kaart', 'bag-panden'],
            title: 'Kadaster op Luchtfoto',
            subtitle: 'Percelen en Gebouwen',
            scale: 1000,
            description: 'Kadastrale percelen met BAG panden op luchtfoto'
        },
        // 3. Kadastrale Kaart Detail
        {
            id: 'page-kadaster',
            layerId: 'kadastrale-kaart',
            overlayLayers: ['bag-panden'],
            title: 'Kadastrale Kaart',
            subtitle: 'Percelen en Panden',
            scale: 500,
            description: 'Gedetailleerde kadastrale kaart'
        },
        // 4. Bestemmingsplan
        {
            id: 'page-bestemmingsplan',
            layerId: 'bestemmingsplan',
            title: 'Bestemmingsplan',
            subtitle: 'Enkelbestemmingen',
            scale: 2500,
            description: 'Geldende enkelbestemmingen'
        },
        // 5. AHN Hoogtekaart
        {
            id: 'page-ahn',
            layerId: 'ahn-dsm',
            title: 'AHN Hoogtekaart',
            subtitle: 'Digital Surface Model',
            scale: 1000,
            description: 'Digitaal hoogtemodel inclusief bebouwing'
        },
        // 6. Luchtfoto Overzicht
        {
            id: 'page-luchtfoto-overview',
            layerId: 'luchtfoto-actueel',
            title: 'Luchtfoto Overzicht',
            subtitle: 'Schaal 1:10.000',
            scale: 10000,
            description: 'Luchtfoto voor regionale context'
        },
        // 7. Luchtfoto Omgeving
        {
            id: 'page-luchtfoto-area',
            layerId: 'luchtfoto-actueel',
            title: 'Luchtfoto Omgeving',
            subtitle: 'Schaal 1:2.500',
            scale: 2500,
            description: 'Luchtfoto van de directe omgeving'
        },
        // 8. Luchtfoto Detail
        {
            id: 'page-luchtfoto-detail',
            layerId: 'luchtfoto-actueel',
            title: 'Luchtfoto Detail',
            subtitle: 'Schaal 1:500',
            scale: 500,
            description: 'Gedetailleerde luchtfoto van de locatie'
        },
        // 9. Bodemkaart
        {
            id: 'page-bodem',
            layerId: 'bodemkaart',
            title: 'Bodemkaart',
            subtitle: 'Bodemtypen',
            scale: 5000,
            description: 'Bodemkundige eenheden'
        },
        // 10. Natura 2000
        {
            id: 'page-natura',
            layerId: 'natura2000',
            title: 'Natuurbescherming',
            subtitle: 'Natura 2000',
            scale: 25000,
            description: 'Beschermde natuurgebieden'
        },
        // 11. Gemeentegrenzen
        {
            id: 'page-gemeente',
            layerId: 'gemeentegrenzen',
            title: 'Bestuurlijke Grenzen',
            subtitle: 'Gemeentegrenzen',
            scale: 25000,
            description: 'Bestuurlijke gebiedsindeling'
        },
        // 12. Samenvatting
        {
            id: 'page-samenvatting',
            layerId: 'samenvatting',
            title: 'Samenvatting',
            subtitle: 'Overzicht en Bronvermelding',
            scale: 5000,
            description: 'Locatiegegevens, coördinaten en databronnen',
            isSummary: true
        }
    ]
};

// Scale configurations for bounding box calculation
// Returns bbox size in meters for A3 landscape
const SCALE_TO_BBOX = {
    500: { width: 210, height: 148 },      // A3 @ 1:500 = 210m x 148m
    1000: { width: 420, height: 297 },     // A3 @ 1:1000 = 420m x 297m
    2500: { width: 1050, height: 742 },    // A3 @ 1:2500 = 1050m x 742m
    5000: { width: 2100, height: 1485 },   // A3 @ 1:5000 = 2.1km x 1.5km
    10000: { width: 4200, height: 2970 },  // A3 @ 1:10000 = 4.2km x 3km
    25000: { width: 10500, height: 7425 }, // A3 @ 1:25000 = 10.5km x 7.4km
    50000: { width: 21000, height: 14850 } // A3 @ 1:50000 = 21km x 15km
};

// Helper function to calculate bounding box from center point
function calculateBBox(centerLat, centerLng, scale, paperSize = 'A3', orientation = 'landscape') {
    const bbox = SCALE_TO_BBOX[scale] || SCALE_TO_BBOX[2500];

    // Adjust for paper size (A4 is ~70% of A3)
    const sizeFactor = paperSize === 'A4' ? 0.707 : 1;

    // Swap width/height for portrait
    let width = orientation === 'portrait' ? bbox.height : bbox.width;
    let height = orientation === 'portrait' ? bbox.width : bbox.height;

    width *= sizeFactor;
    height *= sizeFactor;

    // Convert meters to degrees (approximate for Netherlands)
    // 1 degree latitude ≈ 111,320 meters
    // 1 degree longitude ≈ 111,320 * cos(latitude) meters
    const latDegPerMeter = 1 / 111320;
    const lngDegPerMeter = 1 / (111320 * Math.cos(centerLat * Math.PI / 180));

    const halfWidthDeg = (width / 2) * lngDegPerMeter;
    const halfHeightDeg = (height / 2) * latDegPerMeter;

    return {
        minLng: centerLng - halfWidthDeg,
        minLat: centerLat - halfHeightDeg,
        maxLng: centerLng + halfWidthDeg,
        maxLat: centerLat + halfHeightDeg,
        width: width,
        height: height
    };
}

// Export for use in app.js
window.AVAILABLE_LAYERS = AVAILABLE_LAYERS;
window.DEFAULT_LAYERS = DEFAULT_LAYERS;
window.STANDARD_REPORT = STANDARD_REPORT;
window.SCALE_TO_BBOX = SCALE_TO_BBOX;
window.calculateBBox = calculateBBox;
