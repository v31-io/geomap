<script setup>
import axios from "axios";
import { ref } from "vue";
import { Map, Layers, Sources } from "vue3-openlayers";

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

const urls = ref([])

async function fetchData() {
  const response = await axios.get('/api');
  const tiles = response.data;
  Object.keys(tiles['tiles']).forEach(tile => {
    const id = tiles['tiles'][tile][0]['ID'];
    urls.value.push(`${tiles['base_url']}/${tile}/${id}/rgba.tif`);
  });
}
fetchData()
</script>

<template>
  <Map.OlMap style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;">
    <Map.OlView ref="view" :center="center" :zoom="zoom" :projection="projection"/>

    <Layers.OlWebglTileLayer :zIndex="1001">
      <Sources.OlSourceOsm/>
    </Layers.OlWebglTileLayer>

    <div v-for="(url, index) in urls" :key="index">
      <Layers.OlWebglTileLayer :zIndex="1002" :style="trueColor" :preload="Infinity" :transition="true">
        <Sources.OlSourceGeoTiff :sources="[{url: [url]}]" :transparent="true"/>
      </Layers.OlWebglTileLayer>
    </div>
  </Map.OlMap>
</template>