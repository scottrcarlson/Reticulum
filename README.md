Reticulum Network Stack α
==========

Reticulum is a cryptography-based networking stack for low-bandwidth, high-latency, wide-area networks built on cheap and readily available hardware. Reticulum allows you to build very wide-area networks with cheap off-the-shelf tools, and offers end-to-end encryption, cryptographically backed multi-hop transport, efficient addressing, resource caching, unforgeable packet acknowledgements and much more.

Reticulum is a complete networking stack, and does not use IP or higher layers, although it can be easily tunnelled through conventional IP networks. This frees up a lot of overhead, that has been utilised to implement a networking stack built directly on cryptographic principles, allowing resilience and stable functionality in open and trustless networks.

For more info, see [unsigned.io/projects/reticulum](http://unsigned.io/projects/reticulum/)

## Current Status
Reticulum is currently in pre-alpha state. Even the master branch should be considered experimental. At this point the protocol may change without notice, and is made publicly available for development collaboration, previewing and testing features. Do not build anything serious with Reticulum yet. Stable alpha release will be in early 2019.

## What hardware does Reticulum work with?
Practically any hardware that can support at least a half-duplex channel with 1.000 bits per second throughput, and an MTU of 500 bytes. Data radios, modems, LoRa radios, serial lines, AX.25 TNCs, HAM radio digital modes, free-space optical systems and similar systems are all examples of the types of interfaces Reticulum was designed for.

An open-source LoRa-based interface called [RNode](https://unsigned.io/projects/rnode/) has been designed specifically for use with Reticulum. It is easy to build yourself, or can be purchased as a complete radio that just needs a USB connection to the host.

Reticulum can also be tunneled over existing IP networks.

## Can I use Reticulum for amateur radio?
Some countries still ban the use of encryption when operating under an amateur radio license. Reticulum offers several encryptionless modes, while still using cryptographic principles for station verification, link establishment, data integrity verification, acknowledgements and routing. It is therefore perfectly possible to include Reticulum in amateur radio use, even if your country bans encryption.

## How do I get started?
Full documentation and video tutorials are coming with the stable alpha release. Until then, you are on your own. If you really want to experiment already, you could take a look in the "Examples" folder, for some well-documented example programs. Be sure to also read the [Reticulum Overview Document](http://unsigned.io/wp-content/uploads/2018/04/Reticulum_Overview_v0.4.pdf)

## Dependencies:
 - cryptography.io
 - pyserial 3.1

