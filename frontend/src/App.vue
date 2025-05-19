<script setup>
import axios from "axios"
import { ref, watch } from "vue"
import { Map, Layers, Sources, MapControls, Interactions, Styles } from "vue3-openlayers"
import { useKeycloak } from '@dsb-norge/vue-keycloak-js'
import GeoJSON from 'ol/format/GeoJSON'


const { token } = useKeycloak()
const api = axios.create({
  baseURL: '/api', headers: { Authorization: `Bearer ${token}` }
})
const center = ref([0, 0])
const zoom = ref(2)
const projection = ref("EPSG:4326")

const date = ref(new Date().toISOString().split('T')[0])
const meta = ref({})
const layers = ref({})

watch(date, (newDate) => {
  // Ignore invalid date
  if (new Date(newDate) == NaN || new Date(newDate) < new Date('1997-01-01')) {
    return
  } else {
    fetchLayers()
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

function isEmpty(obj) {
    return Object.keys(obj).length === 0;
}

async function fetchMeta() {
  const response = await api.get('/')
  meta.value = response.data
  fetchLayers()
}

async function fetchLayers() {
  const response = await api.get(`/layers?date=${date.value}`)
  layers.value = response.data.sort((a, b) => a.zlevel - b.zlevel)
}

fetchMeta()
</script>

<template>
  <button v-if="meta.hasOwnProperty('attributions')" type="button" class="attribution-button overlay"
    @click="showAttributions()">Info</button>
  <input type="date" class="date-picker overlay" v-if="!isEmpty(layers)" v-model="date" min="1997-01-01"
    max="2030-01-01" />
  <Map.OlMap class="map">
    <Map.OlView ref="view" :center="center" :zoom="zoom" :projection="projection" />

    <MapControls.OlLayerswitcherControl v-if="layers.length > 0" :reordering="false" />
    <MapControls.OlRotateControl />

    <Layers.OlWebglTileLayer :zIndex="1001" :displayInLayerSwitcher="false">
      <Sources.OlSourceOsm />
    </Layers.OlWebglTileLayer>

    <!-- Data Layers -->
    <Layers.OlLayerGroup v-for="layer in layers" :key="layer['layer']" :title="layer['name']" :visible="layer['visible']">
      <Layers.OlWebglTileLayer v-for="tile in layer['tiles']" :key="tile['tile'] + tile['id']" :displayInLayerSwitcher="false"
        :zIndex="1002" :style="layer['style']" :transition="true">
        <Sources.OlSourceGeoTiff :sources="[{ url: [tile['url']], nodata: NaN, min: layer['min'], max: layer['max'] }]" 
          :transparent="true" />
      </Layers.OlWebglTileLayer>
    </Layers.OlLayerGroup>

    <!-- GLAD ARD Tile Grid Map -->
    <Layers.OlVectorLayer v-if="meta.hasOwnProperty('geojson')" :zIndex="1003" title="GLAD ARD Tiles" :visible="false">
      <Sources.OlSourceVector :features="new GeoJSON().readFeatures(meta['geojson'])" format="geojson" />
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