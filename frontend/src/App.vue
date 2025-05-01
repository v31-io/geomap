<script setup>
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

const url = 'https://3b8f143e486b0ff5cf3d66a77f0077a2.eu.r2.cloudflarestorage.com/v31-store/geomap/glad_ard2/054W_03S/402/rgba.tif?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=83bd44fa5539bb11faf40f5e1ded7736%2F20250501%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250501T130448Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=8a6600adbc396f093b2ff594396e379d5debe8da0c5e9214ca090c130ffb9166'
</script>

<template>
  <Map.OlMap style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;">
    <Map.OlView ref="view" :center="center" :zoom="zoom" :projection="projection"/>

    <Layers.OlWebglTileLayer :zIndex="1001">
      <Sources.OlSourceOsm/>
    </Layers.OlWebglTileLayer>

    <Layers.OlWebglTileLayer :zIndex="1002" :style="trueColor" :preload="Infinity" :transition="true">
      <Sources.OlSourceGeoTiff :sources="[{url: url}]" :transparent="true"/>
    </Layers.OlWebglTileLayer>
  </Map.OlMap>
</template>