<script setup>
import axios from "axios"
import { ref, computed } from "vue"
import { Map, Layers, Sources, MapControls, Interactions, Styles } from "vue3-openlayers"
import { useKeycloak } from '@dsb-norge/vue-keycloak-js'
import GeoJSON from 'ol/format/GeoJSON'


const { keycloak, token } = useKeycloak()
const center = ref([0, 0])
const zoom = ref(2)
const projection = ref("EPSG:4326")

const date = ref(new Date().toISOString().split('T')[0])
const meta = ref({})

const layers = computed(() => {
  if (meta.value.hasOwnProperty('layers')) {
    return meta.value['layers']
  } else {
    return []
  } 
})

const urls = computed((previous) => {
  if (meta.value.hasOwnProperty('tiles')) {
    const _urls = {}
    const tiles = meta.value['tiles']
    const baseUrl = meta.value['base_url']

    // Ignore update
  if (new Date(date.value) == NaN || new Date(date.value) < new Date('1997-01-01')) {
      return previous
    }

    layers.value.forEach((layer) => {
      _urls[layer['layer']] = []
      Object.keys(tiles).forEach(tile => {
        let id = tiles[tile][tiles[tile].length - 1]['ID']
        // Determine closest id to selected date
      if (date.value) {
          const img = tiles[tile].find(img => {
          return new Date(img['Date']) >= new Date(date.value)
          })
          if (img) {
            id = img['ID']
          }
        }
        _urls[layer['layer']].push(`${baseUrl}/${tile}/${id}/${layer['layer']}.tif`)
      })
    })
    return _urls
  } else {
    return {}
  }
})

function showAttributions() {
  alert(meta.value['attributions'])
}

const selectedFeatureText = ref('')
const featureSelected = (event) => {
  if (event.selected.length > 0) {
    const tileID = event.selected[0].getProperties().TILE
    // Prevent event from re-rendering UI
    if (tileID != selectedFeatureText.value)
      selectedFeatureText.value = tileID
  }
}

async function fetchData() {
  await axios.head('/api')
  const response = await axios.get('/api', {
    headers: { Authorization: `Bearer ${token}` }
  })
  meta.value = response.data
}
fetchData()
</script>

<template>
  <button type="button" class="logout-button overlay" @click="keycloak.logout()">Logout</button>
  <button v-if="meta.hasOwnProperty('attributions')" type="button" class="attribution-button overlay" 
    @click="showAttributions()">Info</button>
  <input type="date" class="date-picker overlay" v-if="meta.hasOwnProperty('alltiles')" v-model="date" min="1997-01-01" max="2030-01-01"/>
  <Map.OlMap class="map">
    <Map.OlView ref="view" :center="center" :zoom="zoom" :projection="projection"/>

    <MapControls.OlLayerswitcherControl v-if="layers.length > 0" :reordering="false"/>

    <Layers.OlWebglTileLayer :zIndex="1001" :displayInLayerSwitcher="false">
      <Sources.OlSourceOsm/>
    </Layers.OlWebglTileLayer>
    
    <!-- Data Layers -->
    <Layers.OlLayerGroup v-for="(layer) in layers" :key="layer" :title="layer['name']" :visible="layer['visible']">
      <Layers.OlWebglTileLayer v-for="(url) in urls[layer['layer']]" :key="url"
        :displayInLayerSwitcher="false" :zIndex="1002" :style="layer['style']" :preload="Infinity" :transition="true">
        <Sources.OlSourceGeoTiff :sources="[{url: [url], nodata: NaN}]" :transparent="true" :normalize="layer['normalize']"/>
      </Layers.OlWebglTileLayer>
    </Layers.OlLayerGroup>

    <!-- GLAD ARD Tile Grid Map -->
    <Layers.OlVectorLayer v-if="meta.hasOwnProperty('alltiles')" :zIndex="1003" title="GLAD ARD Tiles" :visible="false">
      <Sources.OlSourceVector :features="new GeoJSON().readFeatures(meta['alltiles'])" format="geojson"/>
    </Layers.OlVectorLayer>

    <!-- Click on GLAD ARD for Tile ID -->
    <Interactions.OlInteractionSelect @select="featureSelected">
      <Styles.OlStyle>
        <Styles.OlStyleText :text="selectedFeatureText" font="20px sans-serif">
          <Styles.OlStyleFill color="red" />
        </Styles.OlStyleText>
        <Styles.OlStyleStroke color="red" :width="5" />
      </Styles.OlStyle>
    </Interactions.OlInteractionSelect>
  </Map.OlMap>
</template>

<style>
.map {
  position: fixed; 
  top: 0; 
  left: 0; 
  width: 100%; 
  height: 100%;
}

.attribution-button {
  bottom: 8px;
  right: 8px;
}

.logout-button {
  top: 8px;
  right: 8px;
}

.date-picker {
  bottom: 8px;
  left: 8px;
}

.overlay {
  position: absolute; 
  z-index: 1000;
  background: white; 
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
</style>