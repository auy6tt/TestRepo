# Software bill of materials: Sprout S1 2.3.0

- **Product:** Sprout S1 (version 2.3.0)
- **Manufacturer:** Mossbyte Labs BV (fictional)
- **SBOM file:** `sprout-s1-2.3.0.cdx.json` (CycloneDX 1.6, JSON)
- **SHA-256 of the SBOM file:** `4f5ab08eeaf59d6b6bf892c7c7d87284c258d0f53277fc0e528fac63fc85e3c2`
- **Generated:** 2026-10-07 by Alex Example, Example Consulting (fictional)
- **Components listed:** 137

> **Please confirm.** This list was produced from the dependency files you provided. Check that it matches the release you actually ship, including firmware libraries and anything copied into the code by hand. Tell us about anything missing or wrong, then confirm in writing. The SBOM stays a draft until you do.

## Parts of the product

| Part | Version | Type | Components |
|---|---|---|---|
| sprout-cloud | 2.3.0 | application | 16 |
| sprout-companion | 2.3.0 | application | 116 |
| sprout-fw | 2.3.0 | firmware | 5 |

## Licences at a glance

Licence names come from package metadata. They can be incomplete or wrong, and this is not a licence review.

| Licence | Components |
|---|---|
| MIT | 115 |
| BSD-3-Clause | 8 |
| ISC | 4 |
| BSD License | 3 |
| Apache-2.0 | 2 |
| 0BSD | 1 |
| Apache Software License | 1 |
| Apache-2.0 OR BSD-2-Clause | 1 |
| MPL-2.0 | 1 |
| OSI-approved (name not stated) | 1 |

Worth a look:

- Copyleft-style licences found (MPL-2.0). These can come with conditions when you distribute the product. Ask your lawyer if unsure.

## Components

### sprout-cloud

| # | Component | Version | Type | Direct? | Licence | Package URL (purl) |
|---|---|---|---|---|---|---|
| 1 | Flask | 2.3.2 | library | Yes | BSD-3-Clause | pkg:pypi/flask@2.3.2 |
| 2 | gunicorn | 21.2.0 | library | Yes | MIT | pkg:pypi/gunicorn@21.2.0 |
| 3 | paho-mqtt | 1.6.1 | library | Yes | OSI-approved (name not stated) | pkg:pypi/paho-mqtt@1.6.1 |
| 4 | python-dotenv | 1.0.1 | library | Yes | BSD-3-Clause | pkg:pypi/python-dotenv@1.0.1 |
| 5 | requests | 2.31.0 | library | Yes | Apache Software License | pkg:pypi/requests@2.31.0 |
| 6 | Werkzeug | 3.0.1 | library | Yes | BSD License | pkg:pypi/werkzeug@3.0.1 |
| 7 | blinker | 1.9.0 | library | No | MIT | pkg:pypi/blinker@1.9.0 |
| 8 | certifi | 2026.7.22 | library | No | MPL-2.0 | pkg:pypi/certifi@2026.7.22 |
| 9 | charset-normalizer | 3.5.2 | library | No | MIT | pkg:pypi/charset-normalizer@3.5.2 |
| 10 | click | 8.5.0 | library | No | BSD-3-Clause | pkg:pypi/click@8.5.0 |
| 11 | idna | 3.20 | library | No | BSD-3-Clause | pkg:pypi/idna@3.20 |
| 12 | itsdangerous | 2.2.0 | library | No | BSD License | pkg:pypi/itsdangerous@2.2.0 |
| 13 | Jinja2 | 3.1.6 | library | No | BSD License | pkg:pypi/jinja2@3.1.6 |
| 14 | MarkupSafe | 3.0.4 | library | No | BSD-3-Clause | pkg:pypi/markupsafe@3.0.4 |
| 15 | packaging | 26.3 | library | No | Apache-2.0 OR BSD-2-Clause | pkg:pypi/packaging@26.3 |
| 16 | urllib3 | 2.8.0 | library | No | MIT | pkg:pypi/urllib3@2.8.0 |

### sprout-companion

| # | Component | Version | Type | Direct? | Licence | Package URL (purl) |
|---|---|---|---|---|---|---|
| 1 | commander | 12.1.0 | library | Yes | MIT | pkg:npm/commander@12.1.0 |
| 2 | express | 4.18.2 | library | Yes | MIT | pkg:npm/express@4.18.2 |
| 3 | mqtt | 5.16.0 | library | Yes | MIT | pkg:npm/mqtt@5.16.0 |
| 4 | @babel/runtime | 7.29.10 | library | No | MIT | pkg:npm/%40babel/runtime@7.29.10 |
| 5 | @types/node | 26.6.4 | library | No | MIT | pkg:npm/%40types/node@26.6.4 |
| 6 | @types/readable-stream | 4.0.25 | library | No | MIT | pkg:npm/%40types/readable-stream@4.0.25 |
| 7 | @types/ws | 8.18.2 | library | No | MIT | pkg:npm/%40types/ws@8.18.2 |
| 8 | abort-controller | 3.0.0 | library | No | MIT | pkg:npm/abort-controller@3.0.0 |
| 9 | accepts | 1.3.8 | library | No | MIT | pkg:npm/accepts@1.3.8 |
| 10 | array-flatten | 1.1.1 | library | No | MIT | pkg:npm/array-flatten@1.1.1 |
| 11 | base64-js | 1.5.1 | library | No | MIT | pkg:npm/base64-js@1.5.1 |
| 12 | bl | 6.1.6 | library | No | MIT | pkg:npm/bl@6.1.6 |
| 13 | body-parser | 1.20.1 | library | No | MIT | pkg:npm/body-parser@1.20.1 |
| 14 | broker-factory | 3.1.15 | library | No | MIT | pkg:npm/broker-factory@3.1.15 |
| 15 | buffer | 6.0.3 | library | No | MIT | pkg:npm/buffer@6.0.3 |
| 16 | buffer-from | 1.1.2 | library | No | MIT | pkg:npm/buffer-from@1.1.2 |
| 17 | bytes | 3.1.2 | library | No | MIT | pkg:npm/bytes@3.1.2 |
| 18 | call-bind-apply-helpers | 1.0.2 | library | No | MIT | pkg:npm/call-bind-apply-helpers@1.0.2 |
| 19 | call-bound | 1.0.4 | library | No | MIT | pkg:npm/call-bound@1.0.4 |
| 20 | commist | 3.2.0 | library | No | MIT | pkg:npm/commist@3.2.0 |
| 21 | concat-stream | 2.0.0 | library | No | MIT | pkg:npm/concat-stream@2.0.0 |
| 22 | content-disposition | 0.5.4 | library | No | MIT | pkg:npm/content-disposition@0.5.4 |
| 23 | content-type | 1.0.5 | library | No | MIT | pkg:npm/content-type@1.0.5 |
| 24 | cookie | 0.5.0 | library | No | MIT | pkg:npm/cookie@0.5.0 |
| 25 | cookie-signature | 1.0.6 | library | No | MIT | pkg:npm/cookie-signature@1.0.6 |
| 26 | debug | 2.6.9 | library | No | MIT | pkg:npm/debug@2.6.9 |
| 27 | debug | 4.4.3 | library | No | MIT | pkg:npm/debug@4.4.3 |
| 28 | debug | 2.6.9 | library | No | MIT | pkg:npm/debug@2.6.9 |
| 29 | debug | 2.6.9 | library | No | MIT | pkg:npm/debug@2.6.9 |
| 30 | debug | 2.6.9 | library | No | MIT | pkg:npm/debug@2.6.9 |
| 31 | depd | 2.0.0 | library | No | MIT | pkg:npm/depd@2.0.0 |
| 32 | destroy | 1.2.0 | library | No | MIT | pkg:npm/destroy@1.2.0 |
| 33 | dunder-proto | 1.0.1 | library | No | MIT | pkg:npm/dunder-proto@1.0.1 |
| 34 | ee-first | 1.1.1 | library | No | MIT | pkg:npm/ee-first@1.1.1 |
| 35 | encodeurl | 1.0.2 | library | No | MIT | pkg:npm/encodeurl@1.0.2 |
| 36 | es-define-property | 1.0.1 | library | No | MIT | pkg:npm/es-define-property@1.0.1 |
| 37 | es-errors | 1.3.0 | library | No | MIT | pkg:npm/es-errors@1.3.0 |
| 38 | es-object-atoms | 1.1.2 | library | No | MIT | pkg:npm/es-object-atoms@1.1.2 |
| 39 | escape-html | 1.0.3 | library | No | MIT | pkg:npm/escape-html@1.0.3 |
| 40 | etag | 1.8.1 | library | No | MIT | pkg:npm/etag@1.8.1 |
| 41 | event-target-shim | 5.0.1 | library | No | MIT | pkg:npm/event-target-shim@5.0.1 |
| 42 | events | 3.3.0 | library | No | MIT | pkg:npm/events@3.3.0 |
| 43 | fast-unique-numbers | 9.0.27 | library | No | MIT | pkg:npm/fast-unique-numbers@9.0.27 |
| 44 | finalhandler | 1.2.0 | library | No | MIT | pkg:npm/finalhandler@1.2.0 |
| 45 | forwarded | 0.2.0 | library | No | MIT | pkg:npm/forwarded@0.2.0 |
| 46 | fresh | 0.5.2 | library | No | MIT | pkg:npm/fresh@0.5.2 |
| 47 | function-bind | 1.1.2 | library | No | MIT | pkg:npm/function-bind@1.1.2 |
| 48 | get-intrinsic | 1.3.0 | library | No | MIT | pkg:npm/get-intrinsic@1.3.0 |
| 49 | get-proto | 1.0.1 | library | No | MIT | pkg:npm/get-proto@1.0.1 |
| 50 | gopd | 1.2.0 | library | No | MIT | pkg:npm/gopd@1.2.0 |
| 51 | has-symbols | 1.1.0 | library | No | MIT | pkg:npm/has-symbols@1.1.0 |
| 52 | hasown | 2.0.4 | library | No | MIT | pkg:npm/hasown@2.0.4 |
| 53 | help-me | 5.0.0 | library | No | MIT | pkg:npm/help-me@5.0.0 |
| 54 | http-errors | 2.0.0 | library | No | MIT | pkg:npm/http-errors@2.0.0 |
| 55 | iconv-lite | 0.4.24 | library | No | MIT | pkg:npm/iconv-lite@0.4.24 |
| 56 | ieee754 | 1.2.1 | library | No | BSD-3-Clause | pkg:npm/ieee754@1.2.1 |
| 57 | inherits | 2.0.4 | library | No | ISC | pkg:npm/inherits@2.0.4 |
| 58 | ip-address | 10.7.3 | library | No | MIT | pkg:npm/ip-address@10.7.3 |
| 59 | ipaddr.js | 1.9.1 | library | No | MIT | pkg:npm/ipaddr.js@1.9.1 |
| 60 | lru-cache | 10.4.3 | library | No | ISC | pkg:npm/lru-cache@10.4.3 |
| 61 | math-intrinsics | 1.1.0 | library | No | MIT | pkg:npm/math-intrinsics@1.1.0 |
| 62 | media-typer | 0.3.0 | library | No | MIT | pkg:npm/media-typer@0.3.0 |
| 63 | merge-descriptors | 1.0.1 | library | No | MIT | pkg:npm/merge-descriptors@1.0.1 |
| 64 | methods | 1.1.2 | library | No | MIT | pkg:npm/methods@1.1.2 |
| 65 | mime | 1.6.0 | library | No | MIT | pkg:npm/mime@1.6.0 |
| 66 | mime-db | 1.52.0 | library | No | MIT | pkg:npm/mime-db@1.52.0 |
| 67 | mime-types | 2.1.35 | library | No | MIT | pkg:npm/mime-types@2.1.35 |
| 68 | minimist | 1.2.8 | library | No | MIT | pkg:npm/minimist@1.2.8 |
| 69 | mqtt-packet | 9.0.2 | library | No | MIT | pkg:npm/mqtt-packet@9.0.2 |
| 70 | ms | 2.0.0 | library | No | MIT | pkg:npm/ms@2.0.0 |
| 71 | ms | 2.1.3 | library | No | MIT | pkg:npm/ms@2.1.3 |
| 72 | ms | 2.0.0 | library | No | MIT | pkg:npm/ms@2.0.0 |
| 73 | ms | 2.0.0 | library | No | MIT | pkg:npm/ms@2.0.0 |
| 74 | ms | 2.0.0 | library | No | MIT | pkg:npm/ms@2.0.0 |
| 75 | negotiator | 0.6.3 | library | No | MIT | pkg:npm/negotiator@0.6.3 |
| 76 | object-inspect | 1.13.4 | library | No | MIT | pkg:npm/object-inspect@1.13.4 |
| 77 | on-finished | 2.4.1 | library | No | MIT | pkg:npm/on-finished@2.4.1 |
| 78 | parseurl | 1.3.3 | library | No | MIT | pkg:npm/parseurl@1.3.3 |
| 79 | path-to-regexp | 0.1.7 | library | No | MIT | pkg:npm/path-to-regexp@0.1.7 |
| 80 | process | 0.11.10 | library | No | MIT | pkg:npm/process@0.11.10 |
| 81 | process-nextick-args | 2.0.1 | library | No | MIT | pkg:npm/process-nextick-args@2.0.1 |
| 82 | proxy-addr | 2.0.8 | library | No | MIT | pkg:npm/proxy-addr@2.0.8 |
| 83 | qs | 6.11.0 | library | No | BSD-3-Clause | pkg:npm/qs@6.11.0 |
| 84 | range-parser | 1.2.1 | library | No | MIT | pkg:npm/range-parser@1.2.1 |
| 85 | raw-body | 2.5.1 | library | No | MIT | pkg:npm/raw-body@2.5.1 |
| 86 | readable-stream | 4.7.0 | library | No | MIT | pkg:npm/readable-stream@4.7.0 |
| 87 | readable-stream | 3.6.2 | library | No | MIT | pkg:npm/readable-stream@3.6.2 |
| 88 | rfdc | 1.4.1 | library | No | MIT | pkg:npm/rfdc@1.4.1 |
| 89 | safe-buffer | 5.2.1 | library | No | MIT | pkg:npm/safe-buffer@5.2.1 |
| 90 | safer-buffer | 2.1.2 | library | No | MIT | pkg:npm/safer-buffer@2.1.2 |
| 91 | send | 0.18.0 | library | No | MIT | pkg:npm/send@0.18.0 |
| 92 | serve-static | 1.15.0 | library | No | MIT | pkg:npm/serve-static@1.15.0 |
| 93 | setprototypeof | 1.2.0 | library | No | ISC | pkg:npm/setprototypeof@1.2.0 |
| 94 | side-channel | 1.1.1 | library | No | MIT | pkg:npm/side-channel@1.1.1 |
| 95 | side-channel-list | 1.0.1 | library | No | MIT | pkg:npm/side-channel-list@1.0.1 |
| 96 | side-channel-map | 1.0.1 | library | No | MIT | pkg:npm/side-channel-map@1.0.1 |
| 97 | side-channel-weakmap | 1.0.2 | library | No | MIT | pkg:npm/side-channel-weakmap@1.0.2 |
| 98 | smart-buffer | 4.2.0 | library | No | MIT | pkg:npm/smart-buffer@4.2.0 |
| 99 | socks | 2.8.10 | library | No | MIT | pkg:npm/socks@2.8.10 |
| 100 | split2 | 4.2.0 | library | No | ISC | pkg:npm/split2@4.2.0 |
| 101 | statuses | 2.0.1 | library | No | MIT | pkg:npm/statuses@2.0.1 |
| 102 | string_decoder | 1.3.0 | library | No | MIT | pkg:npm/string_decoder@1.3.0 |
| 103 | toidentifier | 1.0.1 | library | No | MIT | pkg:npm/toidentifier@1.0.1 |
| 104 | tslib | 2.8.1 | library | No | 0BSD | pkg:npm/tslib@2.8.1 |
| 105 | type-is | 1.6.18 | library | No | MIT | pkg:npm/type-is@1.6.18 |
| 106 | typedarray | 0.0.6 | library | No | MIT | pkg:npm/typedarray@0.0.6 |
| 107 | undici-types | 8.9.0 | library | No | MIT | pkg:npm/undici-types@8.9.0 |
| 108 | unpipe | 1.0.0 | library | No | MIT | pkg:npm/unpipe@1.0.0 |
| 109 | util-deprecate | 1.0.2 | library | No | MIT | pkg:npm/util-deprecate@1.0.2 |
| 110 | utils-merge | 1.0.1 | library | No | MIT | pkg:npm/utils-merge@1.0.1 |
| 111 | vary | 1.1.2 | library | No | MIT | pkg:npm/vary@1.1.2 |
| 112 | worker-factory | 7.0.50 | library | No | MIT | pkg:npm/worker-factory@7.0.50 |
| 113 | worker-timers | 8.0.34 | library | No | MIT | pkg:npm/worker-timers@8.0.34 |
| 114 | worker-timers-broker | 8.0.18 | library | No | MIT | pkg:npm/worker-timers-broker@8.0.18 |
| 115 | worker-timers-worker | 9.0.15 | library | No | MIT | pkg:npm/worker-timers-worker@9.0.15 |
| 116 | ws | 8.22.0 | library | No | MIT | pkg:npm/ws@8.22.0 |

### sprout-fw

| # | Component | Version | Type | Direct? | Licence | Package URL (purl) |
|---|---|---|---|---|---|---|
| 1 | cJSON | 1.7.15 | library | Yes | MIT | pkg:github/DaveGamble/cJSON@v1.7.15 |
| 2 | ESP-IDF | 5.1.2 | framework | Yes | Apache-2.0 | pkg:github/espressif/esp-idf@v5.1.2 |
| 3 | FreeRTOS kernel (ESP-IDF port) | 10.4.3 | operating-system | Yes | MIT |  |
| 4 | lwIP | 2.1.3 | library | Yes | BSD-3-Clause |  |
| 5 | Mbed TLS | 3.4.1 | library | Yes | Apache-2.0 | pkg:github/Mbed-TLS/mbedtls@v3.4.1 |

## How to read this

- **Direct?** Yes means your project asks for this component itself. No means it comes in through another component.
- **Package URL (purl)** is the standard name vulnerability databases use to look a component up.
- The full machine-readable version is the `.cdx.json` file. Keep one per release, together with the release itself.
