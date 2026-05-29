-- Bind static classes from java
StandardCharsets = luajava.bindClass("java.nio.charset.StandardCharsets")
Taxon = luajava.bindClass("org.texttechnologylab.annotation.type.Taxon")

-- This "serialize" function is called to transform the CAS object into a stream that is sent to the annotator
-- Inputs:
--  - inputCas: The actual CAS object to serialize
--  - outputStream: Stream that is sent to the annotator, can be e.g. a string, JSON payload, ...
--  - params: Table/Dictionary of parameters that should be used to configure the annotator
function serialize(inputCas, outputStream, params)
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
--  - inputStream: Stream that is received from the annotator, can be e.g. a string, JSON payload, ...
function deserialize(inputCas, inputStream)
    -- Get string from stream, assume UTF-8 encoding
    local inputString = luajava.newInstance("java.lang.String", inputStream:readAllBytes(), StandardCharsets.UTF_8)

    -- Parse JSON data from string into object
    local results = json.decode(inputString)

    -- Add modification annotation
    local modification_meta = results["modification_meta"]
    if modification_meta ~= nil then
        local modification_anno = luajava.newInstance("org.texttechnologylab.annotation.DocumentModification", inputCas)
        modification_anno:setUser(modification_meta["user"])
        modification_anno:setTimestamp(modification_meta["timestamp"])
        modification_anno:setComment(modification_meta["comment"])
        modification_anno:addToIndexes()
    end

    -- Get meta data, this is the same for every annotation
    local meta = results["meta"]

    -- Add taxons
    local taxons = results["taxons"]
    if taxons ~= nil then
        for i, tax in ipairs(taxons) do
            local taxon_anno = luajava.newInstance("org.texttechnologylab.annotation.type.Taxon", inputCas)
            taxon_anno:setBegin(tax["begin"])
            taxon_anno:setEnd(tax["end"])
            if tax["value"] ~= nil then
                taxon_anno:setValue(tax["value"])
            end
            if tax["identifier"] ~= nil then
                taxon_anno:setIdentifier(tax["identifier"])
            end
            taxon_anno:addToIndexes()

            -- Create meta data for this taxon
            if meta ~= nil then
                local meta_anno = luajava.newInstance("org.texttechnologylab.annotation.AnnotatorMetaData", inputCas)
                meta_anno:setReference(taxon_anno)
                if meta["name"] ~= nil then
                    meta_anno:setName(meta["name"])
                end
                if meta["version"] ~= nil then
                    meta_anno:setVersion(meta["version"])
                end
                if meta["modelName"] ~= nil then
                    meta_anno:setModelName(meta["modelName"])
                end
                if meta["modelVersion"] ~= nil then
                    meta_anno:setModelVersion(meta["modelVersion"])
                end
                meta_anno:addToIndexes()
            end
        end
    end
end
