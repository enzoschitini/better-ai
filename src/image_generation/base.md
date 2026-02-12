┌───────────────────────────────┐
│         GeminiClient 👌       │
├───────────────────────────────┤
│ 1. Init Client (API Key)      │
└───────────────────────────────┘


┌───────────────────────────────┐
│           Validator           │
├───────────────────────────────┤
│ 1. Validate Params            │
│    - model                    │
│    - number_of_images         │
│    - mime_type                │
│    - aspect_ratio             │
│    - image_size               │
│                               │
│ 2. Respeitar defaults         │
│    e limites                  │
│    - max 4 imagens            │
│    - modelos disponíveis      │
│    - etc                      │
└───────────────────────────────┘


┌───────────────────────────────┐
│         FileToBytes           │
├───────────────────────────────┤
│ 1. File Path → Bytes          │
│ 2. Detect Mime Type           │
└───────────────────────────────┘


┌──────────────────────────────────────────────────────────┐
│              ImageGeneratorService 👌                     │
│ (Request: Text / Image Bytes / Image Bytes List, Config)  │
│ → Response: Text, Image Bytes List, Metadata              │
├──────────────────────────────────────────────────────────┤
│ 1. Build Parts (Prompt + Imagens)                          │
│ 2. Config (temperature, top_p, max_tokens, etc)            │
│ 3. Model Call                                              │
│ 4. Response Parse (texto, imagens, metadata)               │
└──────────────────────────────────────────────────────────┘


┌───────────────────────────────┐
│        PayloadBuilder         │
├───────────────────────────────┤
│ 1. Calc Cost                  │
│    - tokens                   │
│    - USD                      │
│                               │
│ 2. MongoDB Payload            │
│    - texto                    │
│    - paths                    │
│    - metadata                 │
│    - cost                     │
│                               │
│ 3. Response Parse + Payload   │
└───────────────────────────────┘


┌───────────────────────────────┐
│          SaveProcess          │
├───────────────────────────────┤
│ 1. Save Images                │
│    - Supabase Storage         │
│                               │
│ 2. Save Metadata              │
│    - MongoDB                  │
└───────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│                        Fluxo Geral                           │
├─────────────────────────────────────────────────────────────┤
│ Validator ─────┐                                            │
│                ├──> ImageEdit ───> PayloadBuilder ───> Save │
│ FileToBytes ───┘           │                                │
│                             └──> GeminiClient               │
└─────────────────────────────────────────────────────────────┘
