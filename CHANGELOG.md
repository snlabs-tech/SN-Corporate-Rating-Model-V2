- Added unit tests for helper functions and integration tests for RatingModel.
## 2026-03-03

### Fixed
- Peer positioning bug: for leverage ratios where lower values are better
  (e.g. debt_ebitda, net_debt_ebitda, debt_equity, debt_capital), the previous
  implementation treated an issuer below the peer average as “worse”, which is
  inverted. The logic now correctly uses LOWER_BETTER_RATIOS: higher-than-peer
  leverage is worse; lower-than-peer coverage/margins is worse.
