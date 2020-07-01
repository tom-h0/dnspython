# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2006, 2007, 2009-2011 Nominum, Inc.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose with or without fee is hereby granted,
# provided that the above copyright notice and this permission notice
# appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND NOMINUM DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL NOMINUM BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import struct
import base64

import dns.exception
import dns.rdtypes.util


class Gateway(dns.rdtypes.util.Gateway):
    name = 'IPSECKEY gateway'

class IPSECKEY(dns.rdata.Rdata):

    """IPSECKEY record"""

    # see: RFC 4025

    __slots__ = ['precedence', 'gateway_type', 'algorithm', 'gateway', 'key']

    def __init__(self, rdclass, rdtype, precedence, gateway_type, algorithm,
                 gateway, key):
        super().__init__(rdclass, rdtype)
        Gateway(gateway_type, gateway).check()
        object.__setattr__(self, 'precedence', precedence)
        object.__setattr__(self, 'gateway_type', gateway_type)
        object.__setattr__(self, 'algorithm', algorithm)
        object.__setattr__(self, 'gateway', gateway)
        object.__setattr__(self, 'key', key)

    def to_text(self, origin=None, relativize=True, **kw):
        gateway = Gateway(self.gateway_type, self.gateway).to_text(origin,
                                                                   relativize)
        return '%d %d %d %s %s' % (self.precedence, self.gateway_type,
                                   self.algorithm, gateway,
                                   dns.rdata._base64ify(self.key))

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True,
                  relativize_to=None):
        precedence = tok.get_uint8()
        gateway_type = tok.get_uint8()
        algorithm = tok.get_uint8()
        gateway = Gateway(gateway_type).from_text(tok, origin, relativize,
                                                  relativize_to)
        b64 = tok.concatenate_remaining_identifiers().encode()
        key = base64.b64decode(b64)
        return cls(rdclass, rdtype, precedence, gateway_type, algorithm,
                   gateway, key)

    def _to_wire(self, file, compress=None, origin=None, canonicalize=False):
        header = struct.pack("!BBB", self.precedence, self.gateway_type,
                             self.algorithm)
        file.write(header)
        Gateway(self.gateway_type, self.gateway).to_wire(file, compress,
                                                         origin, canonicalize)
        file.write(self.key)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        if rdlen < 3:
            raise dns.exception.FormError
        header = struct.unpack('!BBB', wire[current: current + 3])
        gateway_type = header[1]
        current += 3
        rdlen -= 3
        (gateway, cused) = Gateway(gateway_type).from_wire(wire, current,
                                                           rdlen, origin)
        current += cused
        rdlen -= cused
        key = wire[current: current + rdlen].unwrap()
        if origin is not None and gateway_type == 3:
            gateway = gateway.relativize(origin)
        return cls(rdclass, rdtype, header[0], gateway_type, header[2],
                   gateway, key)
