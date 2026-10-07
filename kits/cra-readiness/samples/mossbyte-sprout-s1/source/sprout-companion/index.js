#!/usr/bin/env node
// Sprout Companion: a small desktop tool for the FICTIONAL Sprout S1 plant sensor.
// It listens to sensors on the local MQTT broker, shows a local dashboard and
// syncs readings to the cloud. Small but real, so SBOM tools have work to do.

const { Command } = require('commander');
const express = require('express');
const mqtt = require('mqtt');

const program = new Command();
const latest = new Map();

program
  .name('sprout')
  .description('Companion tool for the Sprout S1 plant sensor')
  .version('2.3.0');

program
  .command('dashboard')
  .description('Show live readings from sensors on your network')
  .option('-b, --broker <url>', 'local MQTT broker', 'mqtts://sprout-hub.local:8883')
  .option('-p, --port <port>', 'dashboard port', '5173')
  .action((opts) => {
    const client = mqtt.connect(opts.broker, { rejectUnauthorized: true });
    client.on('connect', () => client.subscribe('sprout/+/readings'));
    client.on('message', (topic, payload) => {
      try {
        const reading = JSON.parse(payload.toString('utf8'));
        latest.set(String(reading.device_id).slice(0, 64), reading);
      } catch (err) {
        // ignore malformed messages
      }
    });

    const app = express();
    app.get('/api/readings', (req, res) => res.json(Object.fromEntries(latest)));
    app.listen(Number(opts.port), '127.0.0.1', () => {
      console.log(`Dashboard on http://127.0.0.1:${opts.port}`);
    });
  });

program
  .command('sync')
  .description('Upload the latest readings to Sprout Cloud')
  .option('-u, --url <url>', 'cloud API', 'https://api.mossbyte.example/api/v1/readings')
  .action(async (opts) => {
    for (const reading of latest.values()) {
      await fetch(opts.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reading),
        signal: AbortSignal.timeout(5000),
      });
    }
    console.log(`Synced ${latest.size} readings`);
  });

program.parse();
