<script setup>
import axios from "axios";
import { ref } from "vue";
import { Map, Layers, Sources, MapControls } from "vue3-openlayers";

const center = ref([-54.5, -3.5]);
const zoom = ref(10);
const projection = ref("EPSG:4326");

const red = ["band", 1];
const green = ["band", 2];
const blue = ["band", 3];
const alpha = ['band', 4]

const trueColor = ref({
  color: ["array", red, green, blue, alpha],
  gamma: 1.1,
});

const layers = ref([])
const urls = ref({})

async function fetchData() {
  const response = await axios.get('/api');
  const tiles = response.data;

  layers.value = tiles['layers']

  tiles['layers'].forEach((layer) => {
    urls.value[layer['layer']] = []
    Object.keys(tiles['tiles']).forEach(tile => {
      const id = tiles['tiles'][tile][0]['ID'];
      urls.value[layer['layer']].push(`${tiles['base_url']}/${tile}/${id}/${layer['layer']}.tif`);
    })
  })
}
fetchData() 
</script>

<template>
  <Map.OlMap style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;">
    <Map.OlView ref="view" :center="center" :zoom="zoom" :projection="projection"/>

    <MapControls.OlLayerswitcherControl v-if="layers.length > 0" :reordering="false"/>

    <Layers.OlWebglTileLayer :zIndex="1001" :displayInLayerSwitcher="false">
      <Sources.OlSourceOsm/>
    </Layers.OlWebglTileLayer>
    
    <Layers.OlLayerGroup v-for="(layer, layerIndex) in layers" :key="layerIndex" :title="layer['name']">
      <Layers.OlWebglTileLayer v-for="(url, imageIndex) in urls[layer['layer']]" :key="imageIndex" 
        :displayInLayerSwitcher="false" :zIndex="1002" :style="trueColor" :preload="Infinity" :transition="true">
        <Sources.OlSourceGeoTiff :sources="[{url: [url]}]" :transparent="true"/>
      </Layers.OlWebglTileLayer>
    </Layers.OlLayerGroup>
  </Map.OlMap>
</template>