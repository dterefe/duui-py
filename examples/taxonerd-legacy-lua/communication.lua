-- Bind static classes from java
StandardCharsets = luajava.bindClass("java.nio.charset.StandardCharsets")
Taxon = luajava.bindClass("org.texttechnologylab.annotation.type.Taxon")
AnnotationComment = luajava.bindClass("org.texttechnologylab.annotation.AnnotationComment")

-- This "serialize" function is called to transform the CAS object into an stream that is sent to the annotator
-- Inputs:
--  - inputCas: The actual CAS object to serialize
--  - outputStream: Stream that is sent to the annotator, can be e.g. a string, JSON payload, ...
local function parse_list_string(str)
    if str == nil or str == "[]" then
        return {}
    end
    local t = {}
    str = str:gsub("^%[", ""):gsub("%]$", "")
    for item in str:gmatch("'(.-)'") do
        table.insert(t, item)
    end
    if #t == 0 then
        for item in str:gmatch("[^,]+") do
            item = item:gsub("^%s+", ""):gsub("%s+$", ""):gsub("^\"", ""):gsub("\"$", "")
            if item ~= "" then
                table.insert(t, item)
            end
        end
    end
    return t
end

function serialize(inputCas, outputStream, params)
    -- Get data from CAS
    local doc_text = inputCas:getDocumentText()
    local linking = "gbif_backbone"
    local threshold = 0.7
    local exclude = {'tagger', 'parser', 'taxo_abbrev_detector', 'taxon_linker', 'pysbd_sentencizer'}
    local model = "en_ner_eco_md"

    if params ~= nil then
        if params["linking"] ~= nil then
            linking = params["linking"]
        end
        if params["threshold"] ~= nil then
            threshold = params["threshold"]
        end
        if params["model"] ~= nil then
            model = params["model"]
        end
        if params["exclude"] ~= nil then
            local parsed = parse_list_string(params["exclude"])
            if #parsed > 0 then
                exclude = parsed
            else
                exclude = {}
            end
        end
    end

-- Encode data as JSON object and write to stream
    outputStream:write(json.encode({
        text = doc_text,
        linking = linking,
        threshold = threshold,
        exclude = exclude,
        model = model
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

    -- Add sentences
    -- for i, sent in ipairs(results["sentences"]) do
        -- Writing can be disabled via parameters
        -- Note: spaCy will still run the full pipeline, and all results are based on these results

    -- Add taxons
    local taxons = results["taxons"]
    if taxons ~= nil then
        for i, tax in ipairs(taxons) do
            if tax["write_token"] then
                local taxon_anno = luajava.newInstance("org.texttechnologylab.annotation.type.Taxon", inputCas)
                taxon_anno:setBegin(tax["begin"])
                taxon_anno:setEnd(tax["end"])
                taxon_anno:setValue(tax["text"])
                taxon_anno:addToIndexes()

                -- Create meta data for this taxon
                local meta_anno = luajava.newInstance("org.texttechnologylab.annotation.AnnotatorMetaData", inputCas)
                meta_anno:setReference(taxon_anno)
                meta_anno:setName(meta["name"])
                meta_anno:setVersion(meta["version"])
                meta_anno:setModelName(meta["modelName"])
                meta_anno:setModelVersion(meta["modelVersion"])
                meta_anno:addToIndexes()

                -- Add annotation comment for this taxon
                local tax_link = tax["link"]
                if tax_link ~= nil then
                    local anno_comment = luajava.newInstance("org.texttechnologylab.annotation.AnnotationComment", inputCas)
                    anno_comment:setReference(taxon_anno)
                    anno_comment:setKey("link")
                    anno_comment:setValue(tax_link[1])
                    anno_comment:addToIndexes()

                    local anno_comment_1 = luajava.newInstance("org.texttechnologylab.annotation.AnnotationComment", inputCas)
                    anno_comment_1:setReference(taxon_anno)
                    anno_comment_1:setKey("identified_as")
                    anno_comment_1:setValue(tax_link[2])
                    anno_comment_1:addToIndexes()

                    local anno_comment_2 = luajava.newInstance("org.texttechnologylab.annotation.AnnotationComment", inputCas)
                    anno_comment_2:setReference(taxon_anno)
                    anno_comment_2:setKey("similarity")
                    anno_comment_2:setValue(tax_link[3])
                    anno_comment_2:addToIndexes()
                end

                local anno_comment_3 = luajava.newInstance("org.texttechnologylab.annotation.AnnotationComment", inputCas)
                anno_comment_3:setReference(taxon_anno)
                anno_comment_3:setKey("unknown")
                anno_comment_3:setValue(tax["unknown"]) --LIVB
                anno_comment_3:addToIndexes()
            end

        end
    end

end
