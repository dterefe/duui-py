-- Bind static classes from java
StandardCharsets = luajava.bindClass("java.nio.charset.StandardCharsets")
Taxon = luajava.bindClass("org.texttechnologylab.annotation.type.Taxon")
AnnotationComment = luajava.bindClass("org.texttechnologylab.annotation.AnnotationComment")

-- This "serialize" function is called to transform the CAS object into an stream that is sent to the annotator
-- Inputs:
--  - inputCas: The actual CAS object to serialize
--  - outputStream: Stream that is sent to the annotator, can be e.g. a string, JSON payload, ...
function serialize(inputCas, outputStream)
    -- Get data from CAS
    local doc_text = inputCas:getDocumentText()

-- Encode data as JSON object and write to stream
    outputStream:write(json.encode({
        text = doc_text
    }))
end

-- This "deserialize" function is called on receiving the results from the annotator that have to be transformed into a CAS object
-- Inputs:
--  - inputCas: The actual CAS object to deserialize into
--  - inputStream: Stream that is received from to the annotator, can be e.g. a string, JSON payload, ...
function deserialize(inputCas, inputStream)
    -- Get string from stream, assume UTF-8 encoding
    --local inputString = luajava.newInstance(Taxon, inputCas)
    --print(inputStream)
    local inputString = luajava.newInstance("java.lang.String", inputStream:readAllBytes(), StandardCharsets.UTF_8)

    -- Parse JSON data from string into object
    local results = json.decode(inputString)
    print("TaxoNERD:")
    -- Add modification annotation
    local modification_meta = results["modification_meta"]
    local modification_anno = luajava.newInstance("org.texttechnologylab.annotation.DocumentModification", inputCas)
    modification_anno:setUser(modification_meta["user"])
    modification_anno:setTimestamp(modification_meta["timestamp"])
    modification_anno:setComment(modification_meta["comment"])
    modification_anno:addToIndexes()

    -- Get meta data, this is the same for every annotation
    local meta = results["meta"]

    -- Add sentences
    -- for i, sent in ipairs(results["sentences"]) do
        -- Writing can be disabled via parameters
        -- Note: spaCy will still run the full pipeline, and all results are based on these results

    -- Add taxons
    for i, tax in ipairs(results["taxons"]) do
        if tax["write_token"] then
            print("----------------")
            local taxon_anno = luajava.newInstance("org.texttechnologylab.annotation.type.Taxon", inputCas)
            taxon_anno:setBegin(tax["begin"])
            taxon_anno:setEnd(tax["end"])
            taxon_anno:setValue(tax["text"])
            taxon_anno:addToIndexes()

            print(taxon_anno)

            -- Create meta data for this taxon
            local meta_anno = luajava.newInstance("org.texttechnologylab.annotation.AnnotatorMetaData", inputCas)
            meta_anno:setReference(taxon_anno)
            meta_anno:setName(meta["name"])
            meta_anno:setVersion(meta["version"])
            meta_anno:setModelName(meta["modelName"])
            meta_anno:setModelVersion(meta["modelVersion"])
            meta_anno:addToIndexes()

            print(meta_anno)

            -- Add annotation comment for this taxon
            local anno_comment = luajava.newInstance("org.texttechnologylab.annotation.AnnotationComment", inputCas)
            anno_comment:setReference(taxon_anno)
            anno_comment:setKey("link")
            anno_comment:setValue(tax["link"][1])
            anno_comment:addToIndexes()

            local anno_comment_1 = luajava.newInstance("org.texttechnologylab.annotation.AnnotationComment", inputCas)
            anno_comment_1:setReference(taxon_anno)
            anno_comment_1:setKey("identified_as")
            anno_comment_1:setValue(tax["link"][2])
            anno_comment_1:addToIndexes()

            local anno_comment_2 = luajava.newInstance("org.texttechnologylab.annotation.AnnotationComment", inputCas)
            anno_comment_2:setReference(taxon_anno)
            anno_comment_2:setKey("similarity")
            anno_comment_2:setValue(tax["link"][3])
            anno_comment_2:addToIndexes()

            local anno_comment_3 = luajava.newInstance("org.texttechnologylab.annotation.AnnotationComment", inputCas)
            anno_comment_3:setReference(taxon_anno)
            anno_comment_3:setKey("unknown")
            anno_comment_3:setValue(tax["unknown"]) --LIVB
            anno_comment_3:addToIndexes()
            --print("ANNOTATIONCOMMENT")
            print(anno_comment)
            print(anno_comment_1)
            print(anno_comment_2)
            print(anno_comment_3)
        end

    end

end
