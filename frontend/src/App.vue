<script setup>
import axios from "axios";
import { ref, computed } from "vue";
import { Map, Layers, Sources, MapControls } from "vue3-openlayers";

const center = ref([-54.5, -3.5]);
const zoom = ref(9);
const projection = ref("EPSG:4326");

const red = ["band", 1];
const green = ["band", 2];
const blue = ["band", 3];
const alpha = ['band', 4]

const trueColor = ref({
  color: ["array", red, green, blue, alpha],
  gamma: 1.1,
});

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
        let id = tiles[tile][tiles[tile].length - 1]['ID'];
        // Determine closest id to selected date
        if (date.value) {
          const img = tiles[tile].find(img => {
            return new Date(img['Date']) >= new Date(date.value)
          })
          if (img) {
            id = img['ID']
          }
        }
        _urls[layer['layer']].push(`${baseUrl}/${tile}/${id}/${layer['layer']}.tif`);
      })
    })
    return _urls
  } else {
    return {}
  }
})

async function fetchData() {
  const response = await axios.get('/api');
  meta.value = response.data;
}
fetchData()
</script>

<template>
  <input type="date" class="date-picker" v-model="date" min="1997-01-01" max="2030-01-01"/>
  <Map.OlMap style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;">
    <Map.OlView ref="view" :center="center" :zoom="zoom" :projection="projection"/>

    <MapControls.OlLayerswitcherControl v-if="layers.length > 0" :reordering="false"/>

    <Layers.OlWebglTileLayer :zIndex="1001" :displayInLayerSwitcher="false">
      <Sources.OlSourceOsm/>
    </Layers.OlWebglTileLayer>
    
    <Layers.OlLayerGroup v-for="(layer) in layers" :key="layer" :title="layer['name']">
      <Layers.OlWebglTileLayer v-for="(url) in urls[layer['layer']]" :key="url" 
        :displayInLayerSwitcher="false" :zIndex="1002" :style="trueColor" :preload="Infinity" :transition="true">
        <Sources.OlSourceGeoTiff :sources="[{url: [url]}]" :transparent="true"/>
      </Layers.OlWebglTileLayer>
    </Layers.OlLayerGroup>
  </Map.OlMap>
</template>

<style>
.date-picker {
  position: absolute; 
  bottom: 10px;
  left: 10px;
  z-index: 1000;
  background: white; 
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
</style>