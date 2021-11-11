import numpy as np
from stingray.events import EventList
from stingray.varenergyspectrum import VarEnergySpectrum
from stingray.varenergyspectrum import ComplexCovarianceSpectrum, CovarianceSpectrum
from stingray.varenergyspectrum import RmsSpectrum, RmsEnergySpectrum
from stingray.varenergyspectrum import LagSpectrum, LagEnergySpectrum
from stingray.varenergyspectrum import ExcessVarianceSpectrum
from stingray.lightcurve import Lightcurve

from astropy.tests.helper import pytest
np.random.seed(20150907)

class DummyVarEnergy(VarEnergySpectrum):
    def _spectrum_function(self):
        return None, None


class TestExcVarEnergySpectrum(object):
    @classmethod
    def setup_class(cls):
        from ..simulator import Simulator

        simulator = Simulator(0.1, 10000, rms=0.2, mean=200)
        test_lc = simulator.simulate(1)
        cls.test_ev1, cls.test_ev2 = EventList(), EventList()
        cls.test_ev1.simulate_times(test_lc)
        cls.test_ev1.energy = np.random.uniform(0.3, 12,
                                                len(cls.test_ev1.time))

    def test_allocate(self):
        exv = ExcessVarianceSpectrum(self.test_ev1, [0., 100],
                                     (0.3, 12, 5, "lin"),
                                     bin_time=1,
                                     segment_size=100)


class TestVarEnergySpectrum(object):

    @classmethod
    def setup_class(cls):
        tstart = 0.0
        tend = 100.0
        nphot = 1000
        alltimes = np.random.uniform(tstart, tend, nphot)
        alltimes.sort()
        cls.events = EventList(alltimes,
                               energy=np.random.uniform(0.3, 12, nphot),
                               gti = [[tstart, tend]])
        cls.vespec = DummyVarEnergy(cls.events, [0., 10000],
                                    (0.5, 5, 10, "lin"), [0.3, 10],
                                    bin_time=0.1)
        cls.vespeclog = \
            DummyVarEnergy(cls.events, [0., 10000],
                           (0.5, 5, 10, "log"), [0.3, 10])

    def test_intervals_overlapping(self):
        ref_int = self.vespec._decide_ref_intervals([0.5, 6], [0.3, 10])
        np.testing.assert_allclose(ref_int, [[0.3, 0.5], [6, 10]])
        ref_int = self.vespec._decide_ref_intervals([0.5, 11], [0.3, 10])
        np.testing.assert_allclose(ref_int, [[0.3, 0.5]])

    def test_intervals_non_overlapping(self):
        ref_int = self.vespec._decide_ref_intervals([6, 11], [0.3, 5])
        np.testing.assert_allclose(ref_int, [[0.3, 5]])

    def test_ref_band_none(self):
        events = EventList([0.09, 0.21, 0.23, 0.32, 0.4, 0.54],
                           energy=[0,0,0,0,1,1],
                           gti=[[0, 0.65]])
        vespec = DummyVarEnergy(events, [0., 10000],
                                (0, 1, 2, "lin"),
                                bin_time=0.1)
        assert np.allclose(vespec.ref_band, np.array([[0, np.inf]]))

    def test_energy_spec_wrong_list_not_tuple(self):
        events = EventList([0.09, 0.21, 0.23, 0.32, 0.4, 0.54],
                           energy=[0, 0, 0, 0, 1, 1],
                           gti=[[0, 0.65]])
        # Test using a list instead of tuple
        # with pytest.raises(ValueError):
        vespec = DummyVarEnergy(events, [0., 10000],
                                [0, 1, 2, "lin"],
                                bin_time=0.1)

    def test_energy_spec_wrong_str(self):
        events = EventList([0.09, 0.21, 0.23, 0.32, 0.4, 0.54],
                           energy=[0, 0, 0, 0, 1, 1],
                           gti=[[0, 0.65]])
        # Test using a list instead of tuple
        with pytest.raises(ValueError):
            vespec = DummyVarEnergy(events, [0., 10000],
                                    (0, 1, 2, "xxx"),
                                    bin_time=0.1)

    def test_construct_lightcurves(self):
        events = EventList([0.09, 0.21, 0.23, 0.32, 0.4, 0.54],
                           energy=[0,0,0,0,1,1],
                           gti=[[0, 0.65]])
        vespec = DummyVarEnergy(events, [0., 10000],
                                (0, 1, 2, "lin"), [0.5, 1.1],
                                bin_time=0.1)
        base_lc, ref_lc = \
            vespec._construct_lightcurves([0, 0.5],
                                          tstart=0, tstop=0.65)
        np.testing.assert_allclose(base_lc.counts, [1, 0, 2, 1, 0, 0])
        np.testing.assert_allclose(ref_lc.counts, [0, 0, 0, 0, 1, 1])

    def test_construct_lightcurves_no_exclude(self):
        events = EventList([0.09, 0.21, 0.23, 0.32, 0.4, 0.54],
                           energy=[0,0,0,0,1,1],
                           gti=[[0, 0.65]])

        vespec = DummyVarEnergy(events, [0., 10000],
                                (0, 1, 2, "lin"), [0, 0.5],
                                bin_time=0.1)
        base_lc, ref_lc = \
            vespec._construct_lightcurves([0, 0.5],
                                          tstart=0, tstop=0.65,
                                          exclude=False)
        np.testing.assert_equal(base_lc.counts, ref_lc.counts)

    def test_construct_lightcurves_pi(self):
        events = EventList([0.09, 0.21, 0.23, 0.32, 0.4, 0.54],
                           pi=np.asarray([0, 0, 0, 0, 1, 1]),
                           gti=[[0, 0.65]])
        vespec = DummyVarEnergy(events, [0., 10000],
                                (0, 1, 2, "lin"), [0.5, 1.1], use_pi=True,
                                   bin_time=0.1)
        base_lc, ref_lc = \
            vespec._construct_lightcurves([0, 0.5],
                                          tstart=0, tstop=0.65)
        np.testing.assert_allclose(base_lc.counts, [1, 0, 2, 1, 0, 0])
        np.testing.assert_allclose(ref_lc.counts, [0, 0, 0, 0, 1, 1])


class TestRMSEnergySpectrum(object):
    @classmethod
    def setup_class(cls):
        from ..simulator import Simulator
        cls.rms = 0.2
        cls.bin_time = 0.005
        simulator = Simulator(cls.bin_time, 1000, rms=cls.rms, mean=200)
        test_lc = simulator.simulate(1.5)
        test_ev1, test_ev2 = EventList(), EventList()
        test_ev1.simulate_times(test_lc)
        test_ev2.simulate_times(test_lc)
        test_ev1.energy = np.random.uniform(0.3, 12, len(test_ev1.time))
        test_ev2.energy = np.random.uniform(0.3, 12, len(test_ev2.time))

        cls.rmsspec_cross = RmsEnergySpectrum(test_ev1, freq_interval=[0.01, 20.],
                                    energy_spec=(0.3, 12, 2, "lin"),
                                    bin_time=cls.bin_time / 2,
                                    segment_size=2, events2=test_ev2, norm="frac")
        cls.rmsspec_pds = RmsEnergySpectrum(test_ev1, freq_interval=[0.01, 20.],
                                    energy_spec=(0.3, 12, 2, "lin"),
                                    bin_time=cls.bin_time / 2,
                                    segment_size=2, norm="frac")

    def test_correct_rms_values_vs_cross(self):
        """The rms calculated with independent event lists (from the cospectrum)
        is equivalent to the one calculated with one event list (from the PDS)"""
        pds = self.rmsspec_pds.spectrum
        cross = self.rmsspec_cross.spectrum
        err = self.rmsspec_pds.spectrum_error
        cerr = self.rmsspec_cross.spectrum_error
        assert np.allclose(err, cerr, rtol=0.2)
        assert np.allclose(pds, cross, atol=3 * err)

    def test_correct_rms_values(self):
        """The rms is close to 15% (less than 20%, because we do
        not have infinite frequency resolution)"""
        pds = self.rmsspec_pds.spectrum
        err = self.rmsspec_pds.spectrum_error

        assert np.allclose(pds, 0.15, atol=3 * err)

    def test_rms_invalid_evlist_warns(self):
        ev = EventList(time=[], energy=[], gti=self.rmsspec_cross.events1.gti)
        with pytest.warns(UserWarning) as record:
            rms = RmsEnergySpectrum(ev, [0., 100],
                                    (0.3, 12, 5, "lin"),
                                    bin_time=0.01,
                                    segment_size=100,
                                    events2=self.rmsspec_cross.events2)
        assert np.all(np.isnan(rms.spectrum))
        assert np.all(np.isnan(rms.spectrum_error))


class TestCovarianceSpectrum(object):
    @classmethod
    def setup_class(cls):
        from ..simulator import Simulator
        cls.rms = 0.2
        cls.bin_time = 0.005
        simulator = Simulator(cls.bin_time, 1000, rms=cls.rms, mean=200)
        test_lc = simulator.simulate(1.5)
        cls.test_ev1, cls.test_ev2 = EventList(), EventList()
        cls.test_ev1.simulate_times(test_lc)
        cls.test_ev2.simulate_times(test_lc)
        cls.test_ev1.energy = np.random.uniform(0.3, 12, len(cls.test_ev1.time))
        cls.test_ev2.energy = np.random.uniform(0.3, 12, len(cls.test_ev2.time))

    @pytest.mark.parametrize("norm", ["frac", "abs"])
    def test_correct_rms_values_vs_cross(self, norm):
        """The rms calculated with independent event lists (from the cospectrum)
        is equivalent to the one calculated with one event list (from the PDS)"""
        covar = CovarianceSpectrum(self.test_ev1, freq_interval=[0.01, 10.],
                                    energy_spec=(0.3, 12, 2, "lin"),
                                    bin_time=self.bin_time / 2,
                                    segment_size=2, norm=norm,
                                    events2=self.test_ev2)
        rmsspec = RmsSpectrum(self.test_ev1, freq_interval=[0.01, 10.],
                                    energy_spec=(0.3, 12, 2, "lin"),
                                    bin_time=self.bin_time / 2,
                                    segment_size=2, norm=norm)

        cov = covar.spectrum
        rms = rmsspec.spectrum
        coverr = covar.spectrum_error

        assert np.allclose(cov, rms, atol=3 * coverr)

    def test_rms_invalid_evlist_warns(self):
        ev = EventList(time=[], energy=[], gti=self.test_ev1.gti)
        with pytest.warns(UserWarning) as record:
            rms = CovarianceSpectrum(ev, [0., 100],
                                    (0.3, 12, 5, "lin"),
                                    bin_time=0.01,
                                    segment_size=100)
        assert np.all(np.isnan(rms.spectrum))
        assert np.all(np.isnan(rms.spectrum_error))


class TestLagEnergySpectrum(object):
    @classmethod
    def setup_class(cls):
        from ..simulator import Simulator
        dt = 0.01
        cls.time_lag = 0.5
        simulator = Simulator(dt, 4000, rms=0.2, mean=2000)
        test_lc1 = simulator.simulate(2)
        test_lc2 = Lightcurve(test_lc1.time,
                              np.array(np.roll(test_lc1.counts, int(cls.time_lag // dt))),
                              err_dist=test_lc1.err_dist,
                              dt=dt)
        test_ev1, test_ev2 = EventList(), EventList()
        test_ev1.simulate_times(test_lc1)
        test_ev2.simulate_times(test_lc2)

        test_ev1.energy = np.random.uniform(0.3, 9, len(test_ev1.time))
        test_ev2.energy = np.random.uniform(9, 12, len(test_ev2.time))

        cls.lag = LagEnergySpectrum(test_ev1, [0., 1],
                                    (0.3, 9, 3, "lin"), [9, 12],
                                    bin_time=0.01,
                                    segment_size=10,
                                    events2=test_ev2)

    def test_lagspectrum_values_and_errors(self):
        assert np.all(np.abs(self.lag.spectrum - self.time_lag) < \
                      3 * self.lag.spectrum_error)

    def test_lag_invalid_evlist_warns(self):
        ev = EventList(time=[], energy=[], gti=self.lag.events1.gti)
        with pytest.warns(UserWarning) as record:
            lag = LagSpectrum(ev, [0., 0.5],
                            (0.3, 9, 4, "lin"), [9, 12],
                            bin_time=0.1,
                            segment_size=30,
                            events2=self.lag.events2)

        assert np.all(np.isnan(lag.spectrum))
        assert np.all(np.isnan(lag.spectrum_error))
