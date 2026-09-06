# Plant Health Platform Roadmap

This is a living record of the features, architectural decisions, and future ideas planned for the Plant Health Platform.

## Product goals

- Remain useful as a free, local-first personal application.
- Support Ashna and her family first.
- Preserve the option to become a multi-user product later.
- Track each biological plant throughout its entire life.
- Keep historical records when plants move, decline, recover, or die.
- Use evidence, measurements, and outcomes instead of generic plant advice.
- Keep AI providers optional so the application never requires a paid API.

## Privacy principles

- Do not store plant or room photographs by default.
- Process images temporarily and retain structured results only.
- Never commit private plant data, addresses, photographs, or databases to GitHub.
- Make the written street address optional.
- Allow weather calculations to use latitude and longitude without retaining the original address.
- Never automatically search for a home's floor plan using its address.
- Treat extracted room geometry as private information.
- Make room scanning optional.
- Prefer local image and room processing when possible.
- Require users to review AI-generated database changes before saving them.
- Record data source, confidence, and human-verification status.

## Ownership hierarchy

```text
User
  -> Household
      -> Site
          -> Space
              -> Environmental Zone
```

A plant belongs to a household, not permanently to one site. Its location history records movement between homes, rooms, greenhouses, and zones.

## Site information

A site may represent:

- House
- Apartment
- Office
- Greenhouse
- Other future location types

Potential site data includes:

- Optional address
- Latitude and longitude
- Timezone
- Elevation
- Terrain position
- Terrain slope
- Weather provider
- Weather update interval
- Active or inactive status

## Spaces

A space may represent:

- Room
- Basement
- Sunroom
- Greenhouse
- Balcony
- Patio
- Porch
- Grow tent
- Shelf
- Outdoor bed
- Other physical area

Potential space data includes:

- Floor number
- Height above ground
- Below-grade percentage
- Parent space
- Optional future geometry

## Spatial-detail levels

The application should not require users to measure their entire home.

### Level 1: Named zones

Examples:

- South-window table
- Family-room bookshelf
- Greenhouse north bench

This is the default level.

### Level 2: Key measurements

Only request measurements that improve recommendations:

- Plant-to-window distance
- Approximate window size
- Window direction
- Zone height above the floor
- Obstruction level
- Occasional lux readings

### Level 3: Optional phone scan

A supported phone may eventually scan a room and detect:

- Walls
- Windows
- Doors
- Approximate dimensions
- Furniture and obstructions

Camera frames should be deleted after geometry extraction unless the user explicitly chooses to retain them.

### Level 4: Detailed spatial model

Optional future coordinates may describe:

- Windows and skylights
- Plant-placement zones
- Furniture and obstructions
- Plant positions
- Grow lights

This level is intended for advanced light simulation and placement optimization.

## Light system

A room may have multiple light sources, and a zone may receive light from multiple sources.

### Light sources

Supported sources include:

- Windows
- Skylights
- Glass doors
- Grow lights
- Other sources

Potential properties include:

- Orientation in degrees
- Orientation measurement source
- Orientation accuracy
- Width and height
- Sill height
- Glass transmission
- Grow-light wattage
- Color temperature
- Active status

### Zone-to-light-source connection

The connection between a zone and a light source may store:

- Distance
- Clear line of sight
- Estimated contribution weight
- Future obstruction details

## Weather and outdoor conditions

Weather influences available daylight and plant growth.

The application should eventually collect:

- Weather condition code
- Clear, cloudy, partly cloudy, rain, or snow conditions
- Cloud cover
- Precipitation
- Temperature
- Humidity
- Shortwave solar radiation
- Direct solar radiation
- Observation time
- Retrieval time
- Provider
- Observed versus forecast status

The weather provider must be replaceable. Open-Meteo is the planned initial provider for personal development, subject to its current terms.

Weather should be collected once per site rather than separately for every plant.

## Light estimation

Future light estimates may combine:

- Latitude and longitude
- Date and time
- Solar position
- Weather and cloud cover
- Window orientation
- Window area
- Glass transmission
- Outdoor obstructions
- Indoor obstructions
- Distance from each light source
- Actual lux measurements

Measured light should be used to calibrate calculated estimates. The system should communicate uncertainty rather than claiming perfect physical accuracy.

Future summaries may include daily lux-hours or estimated Daily Light Integral.

## Plant records

Reference species information must remain separate from individual plants.

Each individual plant may track:

- Household ownership
- Species
- Nickname
- Acquisition date
- Acquisition source
- Lifecycle status
- Death date
- Suspected cause of death
- Location history
- Container history
- Growing-method history
- Substrate history
- Care history
- Observation history
- Health issues
- Treatments
- Recommendations and outcomes

Dead plants must remain in the database for longitudinal analysis.

## Growing methods and containers

Supported growing methods should include:

- Soil or substrate
- Orchid bark
- Sphagnum moss
- Semi-hydro with LECA
- Pon
- Full water culture
- Mounted
- Bare-root or air culture

Water culture should support:

- Vase, jar, net pot, or reservoir
- Water changes
- Water top-offs
- Nutrient additions
- Root-submersion level
- Optional future pH
- Optional future electrical conductivity
- Optional future dissolved oxygen

## Store-instruction evaluator

When acquiring a plant, the user may enter or photograph the instructions provided by the store.

The system should:

1. Extract individual care claims.
2. Compare them with species information and the plant's actual environment.
3. Rate each claim as safe, caution, high risk, or insufficient evidence.
4. Explain the reasoning.
5. Preserve supporting sources and versions.
6. Allow human review.
7. Record whether the advice was followed.
8. Connect the advice to later plant outcomes.

The system must not assume one growing method, such as water culture, is required for every plant of a species.

## Observations and care

Possible observations include:

- Health score
- Leaf count
- New leaves
- Yellow leaves
- Damaged leaves
- Pest evidence
- Disease evidence
- Root condition
- Soil or substrate moisture
- Growth measurements
- Photographs analyzed
- Human notes

Possible care events include:

- Watering
- Water change
- Fertilizing
- Repotting
- Pruning
- Pest treatment
- Moving
- Propagation
- Cleaning
- Rotating

## Recommendations and outcomes

Every recommendation should be stored with:

- Recommendation type
- Creation date
- Reason
- Confidence
- Accepted, edited, or rejected status
- Completion date
- Measured outcome

This allows the project to evaluate whether its recommendations actually help.

## Natural-language assistant

The user may eventually write:

> Watered the big monstera with 500 mL and noticed two yellow leaves.

A local language model may convert that note into proposed structured actions.

The user must see a preview and confirm it before database changes occur.

The language model must never generate unrestricted SQL for direct execution.

## Image analysis

The image pipeline should support:

- Species suggestions
- Visible-health observations
- Pest or disease suggestions
- Confidence scores
- Human corrections
- Model version
- Optional image retention

Original images should be deleted by default after analysis.

## Machine learning

Different problems require different approaches.

### Computer vision

Use pretrained neural networks and transfer learning for:

- Species classification
- Pest classification
- Disease classification
- Damage detection
- Lesion or pest localization

### Longitudinal plant health

Begin with:

- Rule-based baseline
- Linear or logistic regression
- Random forest
- Gradient boosting
- XGBoost or CatBoost

Do not begin with a deep neural network because the initial personal dataset will be small.

Use grouped and time-based validation to prevent data leakage.

### Optimization

Use mathematical constraint optimization for plant placement. This is separate from machine learning.

Potential constraints include:

- Light requirements
- Temperature
- Humidity
- Available space
- Plant dimensions
- Direct-sun tolerance
- Plants the user does not want moved
- Aesthetic preferences

### Model management

Track:

- Model version
- Training date
- Training rows
- Features
- Evaluation metrics
- Artifact location
- Active model
- Prediction source
- Human correction

## User interface

Begin with Streamlit and Python.

Planned sections include:

- Dashboard
- Plants
- Sites
- Spaces
- Environmental zones
- Tasks
- Observations
- Care events
- Analytics
- Image analysis
- Natural-language assistant

A future commercial application may replace Streamlit with a React or Next.js frontend and a FastAPI backend while preserving the database and business logic.

## Database development

Planned database tools:

- SQLAlchemy
- SQLite for local development
- Alembic migrations
- PostgreSQL if multi-user hosting is needed

The database should support multiple households from the beginning, even while the initial application is used by one family.

## External data and licensing

Maintain records for every external dataset and model:

- Name
- Source
- Version
- License
- Commercial-use permission
- Citation
- Project purpose

Review licenses again before any commercial release.

## Development phases

### Phase 1: Foundation

- [x] Python project setup
- [x] SQLAlchemy base
- [x] Database engine and session
- [x] Users and households
- [x] Sites
- [x] Spaces
- [x] Environmental zones
- [x] Multiple light sources
- [x] Alembic migrations
- [x] Initial local database

### Phase 2: Plant records

- [x] Species
- [x] Individual plants
- [x] Plant lifecycle
- [x] Location history
- [x] Containers
- [x] Growing methods
- [x] Substrates and water culture

### Phase 3: Tracking

- [x] Observations
- [x] Care events
- [x] Health issues
- [x] Treatments
- [x] Tasks
- [x] Recommendations
- [x] Outcomes

### Phase 4: Environment

### Phase 4: Environment

- [x] Weather snapshots
- [x] Weather-provider interface
- [x] Open-Meteo integration
- [x] Manual light measurements
- [x] Light estimation
- [ ] Optional sensors

### Phase 5: Application

#### Completed application foundation

- [x] Streamlit interface
- [x] Household setup
- [x] Site setup with privacy-aware location search
- [x] Room and growing-space setup
- [x] Plant-placement zone setup
- [x] Places hierarchy view
- [x] Places list view
- [x] Rename households, sites, spaces, and zones
- [x] Deactivate sites, spaces, and zones without deleting history
- [x] Add individual plants and assign their initial zones
- [x] Browse and search the plant collection
- [x] Edit plant details and identification

#### Core plant-care workflows

- [ ] Move plants between zones while preserving location history
- [ ] Record care events
- [ ] Complete, snooze, or skip tasks with a recorded reason
- [ ] Build a task-focused Today dashboard
- [ ] Display overdue tasks and plants needing attention
- [ ] Create unified plant profile pages
- [ ] Add quick actions for Water, Observe, Move, Treat, and Add photo
- [ ] Add local plant photograph storage
- [ ] Display plant photographs in grid and list views
- [ ] Add plant health and next-care indicators to collection cards
- [ ] Review plant history in a chronological timeline
- [ ] Compare progress photographs
- [ ] Display container, substrate, care, health, and movement history
- [ ] Add species toxicity and household-safety information
- [ ] Add unit and display preferences
- [ ] View care, health, environment, and outcome analytics

#### Place management

- [ ] Reactivate inactive sites, spaces, and zones
- [ ] Edit place details beyond their names
- [ ] Safely delete place records when appropriate

#### Optional spatial views

- [ ] Optional private floor-plan map
- [ ] Manually draw simple room shapes
- [ ] Optionally upload a user-provided floor plan
- [ ] Drag zones to approximate positions on the map
- [ ] Display plant icons and plant counts by room or zone

### Phase 6: AI and ML

- [ ] Local natural-language parsing
- [ ] Human-confirmation workflow for identification and diagnosis
- [ ] Display identification confidence and alternative matches
- [ ] Local image analysis
- [ ] Public image datasets
- [ ] Computer-vision experiments
- [ ] Guided symptom-recording workflow
- [ ] Context-aware diagnosis using care and environment history
- [ ] Explain possible causes instead of asserting uncertain diagnoses
- [ ] Longitudinal health models
- [ ] Placement optimization
- [ ] Compare outcomes after treatment or relocation
- [ ] Model-version tracking

### Phase 7: Family access and deployment

- [ ] Real user authentication
- [ ] Automatically create a private personal household
- [ ] Family invitations and household joining
- [ ] Owner, admin, caretaker, and member permissions
- [ ] Household-scoped database queries
- [ ] Assign tasks to household members
- [ ] Record which household member performed each care event
- [ ] Household activity feed
- [ ] Temporary caretaker and vacation access
- [ ] Vacation care instructions
- [ ] Household care notifications
- [ ] Hosted PostgreSQL
- [ ] PostgreSQL row-level security
- [ ] Persistent private photo and floor-plan storage
- [ ] Automated database backups
- [ ] Secure private hosting
- [ ] Privacy, export, and deletion controls

### Phase 8: Optional product expansion

- [ ] Mobile room scanning
- [ ] Augmented-reality sunlight visualization
- [ ] Installable mobile web app
- [ ] React or Next.js frontend
- [ ] FastAPI backend
- [ ] Commercial license review
- [ ] Billing only if a commercial product is pursued