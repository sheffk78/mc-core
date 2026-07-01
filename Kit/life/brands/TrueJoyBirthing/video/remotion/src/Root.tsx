// ════════════════════════════════════════════════════════════════════════════
// Root — Remotion entry point, registers all compositions
// ════════════════════════════════════════════════════════════════════════════

import React from 'react';
import { Composition, Folder } from 'remotion';
import { TJB } from './style/tjb-tokens';
import { TJBCityVideo } from './TJBCityVideo';
import { denverData, denverFirstTwoScenes } from './data/denver-example';
import { charlotte_ncData } from './data/charlotte-nc-data';
import { arlington_txData } from './data/arlington-tx-data';
import { st_paul_mnData } from './data/st-paul-mn-data';
import { spokane_waData } from './data/spokane-wa-data';
import { san_jose_caData } from './data/san-jose-ca-data';
import { spring_txData } from './data/spring-tx-data';
import { san_francisco_caData } from './data/san-francisco-ca-data';
import { plano_txData } from './data/plano-tx-data';
import { fresno_caData } from './data/fresno-ca-data';
import { el_paso_txData } from './data/el-paso-tx-data';
import { augusta_gaData } from './data/augusta-ga-data';
import { fort_worth_txData } from './data/fort-worth-tx-data';
import { raleigh_ncData } from './data/raleigh-nc-data';
import { providence_riData } from './data/providence-ri-data';
import { portland_orData } from './data/portland-or-data';
import { meridian_idData } from './data/meridian-id-data';
import { colorado_springs_coData } from './data/colorado-springs-co-data';
import { sacramento_caData } from './data/sacramento-ca-data';
import { pittsburgh_paData } from './data/pittsburgh-pa-data';
import { new_york_nyData } from './data/new-york-ny-data';
import { minneapolis_mnData } from './data/minneapolis-mn-data';
import { las_vegas_nvData } from './data/las-vegas-nv-data';
import { detroit_miData } from './data/detroit-mi-data';
import { san_diego_caData } from './data/san-diego-ca-data';
import { nashville_tnData } from './data/nashville-tn-data';
import { chicago_ilData } from './data/chicago-il-data';
import { phoenix_azData } from './data/phoenix-az-data';
import { los_angeles_caData } from './data/los-angeles-ca-data';
import { miami_flData } from './data/miami-fl-data';
import { san_antonio_txData } from './data/san-antonio-tx-data';
import { baltimore_mdData } from './data/baltimore-md-data';
import { atlanta_gaData } from './data/atlanta-ga-data';
import { philadelphia_paData } from './data/philadelphia-pa-data';
import { seattle_waData } from './data/seattle-wa-data';
import { mckinney_txData } from './data/mckinney-tx-data';
import { conroe_txData } from './data/conroe-tx-data';
import { killeen_txData } from './data/killeen-tx-data';
import { waco_txData } from './data/waco-tx-data';
import { carrollton_txData } from './data/carrollton-tx-data';
import { moreno_valley_caData } from './data/moreno-valley-ca-data';
import { fontana_caData } from './data/fontana-ca-data';
import { dallas_txData } from './data/dallas-tx-data';
import { austin_txData } from './data/austin-tx-data';
import { cary_ncData } from './data/cary-nc-data';
import { fremont_caData } from './data/fremont-ca-data';
import { norfolk_vaData } from './data/norfolk-va-data';
import { tacomaWaData } from './data/tacoma-wa-data';
import { vancouver_waData } from './data/vancouver-wa-data';
import { chesapeake_vaData } from './data/chesapeake-va-data';
import { san_bernardino_caData } from './data/san-bernardino-ca-data';
import { beaumont_txData } from './data/beaumont-tx-data';
import { tyler_txData } from './data/tyler-tx-data';
import { orlando_flData } from './data/orlando-fl-data';
import { tampa_flData } from './data/tampa-fl-data';
import {
  CityHookSlide,
  CityBridgeSlide,
  HospitalCardSlide,
  ProviderPortraitSlide,
  AppFeatureSlide,
  CostRevealSlide,
  InsuranceBranchSlide,
  ProviderGridSlide,
  ProviderScrollSlide,
  CityCTASlide,
} from './scenes/index';

const fps = 30;

// Full Denver video
const totalFrames = denverData.scenes.reduce(
  (sum: number, s: { duration_seconds: number }) => sum + Math.max(Math.ceil(s.duration_seconds * fps), 1),
  0
);

// First-two-scenes test (54s of audio)
const firstTwoFrames = denverFirstTwoScenes.scenes.reduce(
  (sum: number, s: { duration_seconds: number }) => sum + Math.max(Math.ceil(s.duration_seconds * fps), 1),
  0
);

export const Root: React.FC = () => {
  return (
    <>
      <Folder name="TJB-City-Videos">
        <Composition
          id="Tacoma-City-Guide"
          component={TJBCityVideo}
          durationInFrames={tacomaWaData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: tacomaWaData, audioPath: 'audio/tacoma-wa/tacoma-wa-master.wav'}}
        />


        <Composition
          id="Vancouver-City-Guide"
          component={TJBCityVideo}
          durationInFrames={vancouver_waData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: vancouver_waData, audioPath: 'audio/vancouver-wa/vancouver-wa-master.wav'}}
        />
        <Composition
          id="norfolk-va-City-Guide"
          component={TJBCityVideo}
          durationInFrames={norfolk_vaData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: norfolk_vaData, audioPath: 'audio/norfolk-va/norfolk-va-master.wav'}}
        />

        <Composition
          id="fremont-ca-City-Guide"
          component={TJBCityVideo}
          durationInFrames={fremont_caData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: fremont_caData, audioPath: 'audio/fremont-ca/fremont-master.wav'}}
        />

        <Composition
          id="cary-nc-City-Guide"
          component={TJBCityVideo}
          durationInFrames={cary_ncData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: cary_ncData, audioPath: 'audio/cary-nc/cary-nc-master.wav'}}
        />

        <Composition
          id="dallas-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={dallas_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: dallas_txData, audioPath: 'audio/dallas-tx/dallas-tx-master.wav'}}
        />

        <Composition
          id="austin-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={austin_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: austin_txData, audioPath: 'audio/austin-tx/austin-tx-master.wav'}}
        />

        <Composition
          id="fontana-ca-City-Guide"
          component={TJBCityVideo}
          durationInFrames={fontana_caData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: fontana_caData, audioPath: 'audio/fontana-ca/fontana-ca-master.wav'}}
        />
        <Composition
          id="chesapeake-va-City-Guide"
          component={TJBCityVideo}
          durationInFrames={chesapeake_vaData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: chesapeake_vaData, audioPath: 'audio/chesapeake-va/chesapeake-va-master.wav'}}
        />

        <Composition
          id="san-bernardino-ca-City-Guide"
          component={TJBCityVideo}
          durationInFrames={san_bernardino_caData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: san_bernardino_caData, audioPath: 'audio/san-bernardino-ca/san-bernardino-ca-master.wav'}}
        />

        <Composition
          id="moreno-valley-ca-City-Guide"
          component={TJBCityVideo}
          durationInFrames={moreno_valley_caData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: moreno_valley_caData, audioPath: 'audio/moreno-valley-ca/moreno-valley-ca-master.wav'}}
        />

        <Composition
          id="carrollton-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={carrollton_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: carrollton_txData, audioPath: 'audio/carrollton-tx/carrollton-tx-master.wav'}}
        />
        <Composition
          id="beaumont-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={beaumont_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: beaumont_txData, audioPath: 'audio/beaumont-tx/beaumont-tx-master.wav'}}
        />

        <Composition
          id="waco-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={waco_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: waco_txData, audioPath: 'audio/waco-tx/waco-tx-master.wav'}}
        />

        <Composition
          id="killeen-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={killeen_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: killeen_txData, audioPath: 'audio/killeen-tx/killeen-tx-master.wav'}}
        />
        <Composition
          id="tyler-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={tyler_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: tyler_txData, audioPath: 'audio/tyler-tx/tyler-tx-master.wav'}}
        />


        <Composition
          id="conroe-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={conroe_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: conroe_txData, audioPath: 'audio/conroe-tx/conroe-tx-master.wav'}}
        />
        <Composition
          id="mckinney-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={mckinney_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: mckinney_txData, audioPath: 'audio/mckinney-tx/mckinney-tx-master.wav'}}
        />

        <Composition
          id="seattle-wa-City-Guide"
          component={TJBCityVideo}
          durationInFrames={seattle_waData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: seattle_waData, audioPath: 'audio/seattle-wa/seattle-wa-master.wav'}}
        />

        <Composition
          id="philadelphia-pa-City-Guide"
          component={TJBCityVideo}
          durationInFrames={philadelphia_paData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: philadelphia_paData, audioPath: 'audio/philadelphia-pa/philadelphia-pa-master.wav'}}
        />

        <Composition
          id="atlanta-ga-City-Guide"
          component={TJBCityVideo}
          durationInFrames={atlanta_gaData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: atlanta_gaData, audioPath: 'audio/atlanta-ga/atlanta-ga-master.wav'}}
        />

        <Composition
          id="baltimore-md-City-Guide"
          component={TJBCityVideo}
          durationInFrames={baltimore_mdData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: baltimore_mdData, audioPath: 'audio/baltimore-md/baltimore-md-master.wav'}}
        />

        <Composition
          id="san-antonio-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={san_antonio_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: san_antonio_txData, audioPath: 'audio/san-antonio-tx/san-antonio-tx-master.wav'}}
        />

        <Composition
          id="miami-fl-City-Guide"
          component={TJBCityVideo}
          durationInFrames={miami_flData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: miami_flData, audioPath: 'audio/miami-fl/miami-fl-master.wav'}}
        />

        <Composition
          id="los-angeles-ca-City-Guide"
          component={TJBCityVideo}
          durationInFrames={los_angeles_caData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: los_angeles_caData, audioPath: 'audio/los-angeles-ca/los-angeles-ca-master.wav'}}
        />

        <Composition
          id="phoenix-az-City-Guide"
          component={TJBCityVideo}
          durationInFrames={phoenix_azData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: phoenix_azData, audioPath: 'audio/phoenix-az/phoenix-az-master.wav'}}
        />

        <Composition
          id="chicago-il-City-Guide"
          component={TJBCityVideo}
          durationInFrames={chicago_ilData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: chicago_ilData, audioPath: 'audio/chicago-il/chicago-il-master.wav'}}
        />

        <Composition
          id="nashville-tn-City-Guide"
          component={TJBCityVideo}
          durationInFrames={nashville_tnData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: nashville_tnData, audioPath: 'audio/nashville-tn/nashville-tn-master.wav'}}
        />

        <Composition
          id="san-diego-ca-City-Guide"
          component={TJBCityVideo}
          durationInFrames={san_diego_caData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: san_diego_caData, audioPath: 'audio/san-diego-ca/san-diego-ca-master.wav'}}
        />

        <Composition
          id="detroit-mi-City-Guide"
          component={TJBCityVideo}
          durationInFrames={detroit_miData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: detroit_miData, audioPath: 'audio/detroit-mi/detroit-mi-master.wav'}}
        />

        <Composition
          id="las-vegas-nv-City-Guide"
          component={TJBCityVideo}
          durationInFrames={las_vegas_nvData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: las_vegas_nvData, audioPath: 'audio/las-vegas-nv/las-vegas-nv-master.wav'}}
        />

        <Composition
          id="minneapolis-mn-City-Guide"
          component={TJBCityVideo}
          durationInFrames={minneapolis_mnData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: minneapolis_mnData, audioPath: 'audio/minneapolis-mn/minneapolis-mn-master.wav'}}
        />

        <Composition
          id="new-york-ny-City-Guide"
          component={TJBCityVideo}
          durationInFrames={new_york_nyData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: new_york_nyData, audioPath: 'audio/new-york-ny/new-york-ny-master.wav'}}
        />

        <Composition
          id="pittsburgh-pa-City-Guide"
          component={TJBCityVideo}
          durationInFrames={pittsburgh_paData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: pittsburgh_paData, audioPath: 'audio/pittsburgh-pa/pittsburgh-pa-master.wav'}}
        />

        <Composition
          id="sacramento-ca-City-Guide"
          component={TJBCityVideo}
          durationInFrames={sacramento_caData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: sacramento_caData, audioPath: 'audio/sacramento-ca/sacramento-ca-master.wav'}}
        />

        <Composition
          id="colorado-springs-co-City-Guide"
          component={TJBCityVideo}
          durationInFrames={colorado_springs_coData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: colorado_springs_coData, audioPath: 'audio/colorado-springs-co/colorado-springs-co-master.wav'}}
        />

        <Composition
          id="meridian-id-City-Guide"
          component={TJBCityVideo}
          durationInFrames={meridian_idData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: meridian_idData, audioPath: 'audio/meridian-id/meridian-id-master.wav'}}
        />

        <Composition
          id="portland-or-City-Guide"
          component={TJBCityVideo}
          durationInFrames={portland_orData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: portland_orData, audioPath: 'audio/portland-or/portland-or-master.wav'}}
        />

        <Composition
          id="providence-ri-City-Guide"
          component={TJBCityVideo}
          durationInFrames={providence_riData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: providence_riData, audioPath: 'audio/providence-ri/providence-ri-master.wav'}}
        />

        <Composition
          id="raleigh-nc-City-Guide"
          component={TJBCityVideo}
          durationInFrames={raleigh_ncData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: raleigh_ncData, audioPath: 'audio/raleigh-nc/raleigh-nc-master.wav'}}
        />

        <Composition
          id="fort-worth-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={fort_worth_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: fort_worth_txData, audioPath: 'audio/fort-worth-tx/fort-worth-tx-master.wav'}}
        />

        <Composition
          id="augusta-ga-City-Guide"
          component={TJBCityVideo}
          durationInFrames={augusta_gaData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: augusta_gaData, audioPath: 'audio/augusta-ga/augusta-ga-master.wav'}}
        />

        <Composition
          id="el-paso-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={el_paso_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: el_paso_txData, audioPath: 'audio/el-paso-tx/el-paso-tx-master.wav'}}
        />

        <Composition
          id="fresno-ca-City-Guide"
          component={TJBCityVideo}
          durationInFrames={fresno_caData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: fresno_caData, audioPath: 'audio/fresno-ca/fresno-ca-master.wav'}}
        />

        <Composition
          id="plano-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={plano_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: plano_txData, audioPath: 'audio/plano-tx/plano-tx-master.wav'}}
        />

        <Composition
          id="san-francisco-ca-City-Guide"
          component={TJBCityVideo}
          durationInFrames={san_francisco_caData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: san_francisco_caData, audioPath: 'audio/san-francisco-ca/san-francisco-ca-master.wav'}}
        />

        <Composition
          id="spring-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={spring_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: spring_txData, audioPath: 'audio/spring-tx/spring-tx-master.wav'}}
        />

        <Composition
          id="san-jose-ca-City-Guide"
          component={TJBCityVideo}
          durationInFrames={san_jose_caData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: san_jose_caData, audioPath: 'audio/san-jose-ca/san-jose-ca-master.wav'}}
        />

        <Composition
          id="spokane-wa-City-Guide"
          component={TJBCityVideo}
          durationInFrames={spokane_waData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: spokane_waData, audioPath: 'audio/spokane-wa/spokane-wa-master.wav'}}
        />

        <Composition
          id="st-paul-mn-City-Guide"
          component={TJBCityVideo}
          durationInFrames={st_paul_mnData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: st_paul_mnData, audioPath: 'audio/st-paul-mn/st-paul-mn-master.wav'}}
        />

        <Composition
          id="arlington-tx-City-Guide"
          component={TJBCityVideo}
          durationInFrames={arlington_txData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: arlington_txData, audioPath: 'audio/arlington-tx/arlington-tx-master.wav'}}
        />

        <Composition
          id="charlotte-nc-City-Guide"
          component={TJBCityVideo}
          durationInFrames={charlotte_ncData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: charlotte_ncData, audioPath: 'audio/charlotte-nc/charlotte-nc-master.wav'}}
        />
        <Composition
          id="Denver-City-Guide"
          component={TJBCityVideo}
          durationInFrames={totalFrames}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{
            videoData: denverData,
            audioPath: 'audio/denver-co/denver-master.wav',
          }}
        />

        <Composition
          id="orlando-fl-City-Guide"
          component={TJBCityVideo}
          durationInFrames={orlando_flData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{
            videoData: orlando_flData,
            audioPath: 'audio/orlando-fl/orlando-fl-master.wav',
          }}
        />

        <Composition
          id="tampa-fl-City-Guide"
          component={TJBCityVideo}
          durationInFrames={tampa_flData.scenes.reduce((s, c) => s + Math.max(Math.ceil(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{
            videoData: tampa_flData,
            audioPath: 'audio/tampa-fl/tampa-fl-master.wav',
          }}
        />

        <Composition
          id="Denver-60s-Test"
          component={TJBCityVideo}
          durationInFrames={firstTwoFrames}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{
            videoData: denverFirstTwoScenes,
            audioPath: 'audio/denver-co/denver-master.wav',
          }}
        />

        {/* ── Individual slide test compositions ── */}
        <Composition
          id="test-app-section"
          component={TJBCityVideo}
          durationInFrames={Math.ceil(24.00 * 30)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{
            videoData: {
              video_metadata: {
                title: "App Section Test",
                city: "Denver",
                state: "CO",
                slug: "denver-co",
                duration_seconds: 24.00,
                fps: 30,
                medicaid: true,
                hasBirthCenter: false,
                hasAppScreenshot: false,
              },
              scenes: [denverData.scenes.find(s => s.scene_id === "04_app")!],
            },
            audioPath: 'audio/denver-co/denver-master.wav',
          }}
        />

        <Composition
          id="test-city-hook"
          component={() => <CityHookSlide city="Denver" state="Colorado" slug="denver-co" subtitle="Your Birth Planning Guide" skylineImage="images/denver-co-birth-doula-skyline.webp" />}
          durationInFrames={90}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-city-bridge"
          component={() => <CityBridgeSlide city="Denver" state="Colorado" slug="denver-co" />}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-hospital-card"
          component={() => (
            <HospitalCardSlide
              name="UCHealth University of Colorado Hospital"
              address="12605 E 16th Ave, Aurora, CO 80045"
              nicuLevel="III"
              photo="images/denver-uchealth-hospital.webp"
              badges={["Level III NICU", "Doula-Friendly", "Medicaid", "VBAC Supported"]}
              description="The region's academic medical center and highest-level NICU provider in the state. VBAC is supported, doulas welcome as part of the care team."
            />
          )}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-portrait-verified"
          component={() => (
            <ProviderPortraitSlide
              name="Sonja Spitzer"
              practice="Embrace Birth Services"
              photo="images/doulas/sonja-spitzer.webp"
              isVerified={true}
              isMidwife={false}
              description="Former family law attorney turned doula. CAPPA certified postpartum doula. Offers birth and postpartum support."
              costRange="$1,200\u2013$1,900"
              serviceArea={["Denver", "Golden", "Lakewood"]}
              acceptingClients={true}
              services={["Birth Doula", "Postpartum Doula", "Childbirth Education"]}
            />
          )}
          durationInFrames={90}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-portrait-midwife"
          component={() => (
            <ProviderPortraitSlide
              name="Melissa Sexton & Samantha Venn"
              practice="Meadowsweet Midwifery"
              photo="images/doulas/meadowsweet-midwifery.webp"
              isVerified={true}
              isMidwife={true}
              description="Home birth midwifery practice serving Denver since 2010. Offering prenatal, birth, and postpartum care."
              costRange="$6,500 (global fee)"
              serviceArea={["Denver", "Lakewood", "Arvada"]}
              acceptingClients={true}
              services={["Home Birth", "Prenatal Care", "Postpartum Care", "Water Birth"]}
            />
          )}
          durationInFrames={90}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-app-feature"
          component={() => (
            <AppFeatureSlide
              headline="Build Your Birth Plan"
              features={[
                "Nine guided sections — hospital preferences, pain management, who's in the room",
                "Find and connect with doulas and midwives near you",
                "Export a PDF to share with your provider",
                "Free. No account needed. Works on iPhone.",
              ]}
              subtitle="Free \u00b7 No account needed"
            />
          )}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-cost-reveal"
          component={() => (
            <CostRevealSlide
              costRange="$1,000\u2013$3,000"
              label="Average doula cost in Denver"
              description="Most doulas offer payment plans. Start interviewing around week 20, book by week 28."
            />
          )}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-insurance-covers"
          component={() => (
            <InsuranceBranchSlide
              branch="covers"
              stateName="Colorado"
              headline="Medicaid Covers Doulas in Colorado"
              detail="Health First Colorado (the state's Medicaid program) reimburses doulas up to $750 per birth for a full spectrum doula package: prenatal, labor, and postpartum visits."
              policyBadge="HB 23-1027"
              amount="$750/birth"
              phoneNumber="1-800-221-3943"
            />
          )}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-insurance-no-coverage"
          component={() => (
            <InsuranceBranchSlide
              branch="no_coverage"
              stateName="Georgia"
              headline="Georgia Medicaid Doesn't Cover Doulas Right Now"
              detail="Most doulas offer sliding-scale fees and payment plans. Ask when you interview. The Joyful Birth Plan app is always free, no matter what."
            />
          )}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-provider-grid"
          component={() => (
            <ProviderGridSlide
              photos={[
                { photo: 'images/doulas/sonja-spitzer.webp', name: 'Sonja Spitzer' },
                { photo: 'images/doulas/meadowsweet-midwifery.webp', name: 'Melissa Sexton' },
                { name: 'Jane Doe' },
                { name: 'Maria Garcia' },
                { photo: 'images/doulas/sonja-spitzer.webp', name: 'Another Provider' },
                { name: 'Kim Lee' },
                { name: 'Sarah Chen' },
                { photo: 'images/doulas/meadowsweet-midwifery.webp', name: 'River Johnson' },
                { name: 'Lisa Park' },
                { name: 'Tanya Brown' },
                { name: 'Rachel White' },
                { name: 'Amy Stone' },
              ]}
              providerCount={26}
            />
          )}
          durationInFrames={150}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-provider-scroll"
          component={() => (
            <ProviderScrollSlide
              screenshotPath="images/fremont-fullpage-scroll.png"
              providerCount={33}
              maxScroll={5200}
              city="Fremont"
            />
          )}
          durationInFrames={Math.ceil(13.97 * 30)}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-city-cta"
          component={() => (
            <CityCTASlide
              city="Denver"
              slug="denver-co"
            />
          )}
          durationInFrames={90}
          fps={fps}
          width={1920}
          height={1080}
        />
      </Folder>
    </>
  );
};