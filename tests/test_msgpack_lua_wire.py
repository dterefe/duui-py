import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    Domain,
    DomainSpec,
    DuuiResult,
    IODescriptor,
    WireSettings,
)
from duui_py.models.config import WireWindowSettings
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.types import (
    Lemma,
    Token,
)


TOKEN_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"
LEMMA_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma"


def config(protocol: str, compression: str = "none") -> AnnotatorConfig:
    return AnnotatorConfig(
        meta=AnnotatorMeta(),
        descriptor=AnnotatorDescriptor(
            name="wire-test",
            version="1",
            input=IODescriptor(
                text=DomainSpec(
                    default=Domain(mimeType="text/plain; charset=utf-8")
                )
            ),
            output=IODescriptor(
                types={"Token": [TOKEN_TYPE], "Lemma": [LEMMA_TYPE]},
                text=DomainSpec(
                    default=Domain(mimeType="text/plain; charset=utf-8")
                ),
            ),
        ),
        wire=WireSettings(
            protocol=protocol,
            compression=compression,
            window=WireWindowSettings(maxRows=2, maxBytes=4096, flushMs=0),
        ),
    )


class MsgPackLuaWireTest(unittest.TestCase):
    def test_row_batch_round_trips_descriptor_ids_and_features(self):
        codec = MsgPackLuaCodec(config("msgpack-row-batch"))
        body = codec.encode_response(
            DuuiResult(
                annotations=[
                    Token(begin=0, end=3, order=1, ref=10),
                    Lemma(begin=0, end=3, value="der", ref=11),
                ]
            )
        )

        decoded = codec.decode_request(body)
        self.assertEqual([item.type for item in decoded.fs], [TOKEN_TYPE, LEMMA_TYPE])
        self.assertEqual(decoded.fs[0].features["order"], 1)
        self.assertEqual(decoded.fs[1].features["value"], "der")
        self.assertLess(body.count(TOKEN_TYPE.encode()), 2)
        self.assertLess(body.count(b"order"), 2)

    def test_columnar_round_trips_multiple_rows(self):
        codec = MsgPackLuaCodec(config("msgpack-columnar"))
        body = codec.encode_response(
            DuuiResult(
                annotations=[
                    Token(begin=0, end=3, order=1),
                    Token(begin=4, end=10, order=2),
                ]
            )
        )

        decoded = codec.decode_request(body)
        self.assertEqual(len(decoded.fs), 2)
        self.assertEqual([item.begin for item in decoded.fs], [0, 4])
        self.assertEqual([item.features["order"] for item in decoded.fs], [1, 2])

    def test_compressed_columnar_round_trips_with_builtin_zlib(self):
        codec = MsgPackLuaCodec(config("compressed-msgpack-columnar", "zlib"))
        body = codec.encode_response(
            DuuiResult(
                annotations=[Token(begin=i, end=i + 1, order=i) for i in range(20)]
            )
        )

        decoded = codec.decode_request(body)
        self.assertEqual(len(decoded.fs), 20)
        self.assertEqual(decoded.fs[-1].features["order"], 19)


if __name__ == "__main__":
    unittest.main()
