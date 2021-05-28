import logging

from api.models import StatementOfVaccination, StepTwoData
from api.signers.eu_international import sign as eu_sign
from api.signers.nl_domestic_dynamic import sign as nl_sign
from api.tests.test_eusigner import vaccination_events

log = logging.getLogger(__package__)

"""
How to get this to work:
1: git clone https://github.com/minvws/nl-covid19-coronacheck-hcert-private
2: cd nl-covid19-coronacheck-hcert-private
3: Add certificates Health_DSC_valid_for_vaccinations.key and Health_DSC_valid_for_vaccinations.pem (todo: commands?)
4: go run ./ server
5: make example
"""

issue_commitment_message = """
{
  "n_2": "chMLFreGBi4t2obBcLDf/A==",
  "combinedProofs": [
    {
      "U": "fFuFoBj9D+M7ifx3aWiumP0bKNeQQ1sdvtuJVJzn38+CDM4kkilYyMBAux0I8gdmdcm1HdUSHDXseQFQXKrpVWkcWZswTx2EgZ344NrZOcbimuW4PCAFEgbmEEVc7LsjEdkp/nODutJtaykJD4FHn1R7bf+VXjlYvPMkeosacMvs0c4bkao7crc+9AncfHqZC1LUlQYIDSM2HvQs0AXqa2urTCBcaPyxPGJDUafTRuWRLClReuKlxPG+Mxw5wLZGGFZDnrO2+D4iIQQsMsoSXjo6BXPqa9wD+Tm9FYE08l4olW92marRyqtW3YMnIWrO61sCHGp6BLGtTiCHKaZPng==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "0g+PwQIveSwJjHs11yC5gTXeNPJFzyR34XF0O+ARkZEP2U/C1NWAnqpUalcjsZbxacj0H+41f/BrKaZqtFp0gI2LmfnJxxRWnfif8KdXs+DKsr5oaRykx32YxOXRZgX28C01RINJv1akGIK0yPw4CKY5lcWdBO4O6nYI//JgHI4Uot8yxISNSzqJdFJ4graahzqrw5xH14eEoSM5ysr4kTT0Fc4o7sd3WElUymcqdqLN24rb2qFEk7LONVgkLNWCbXKtDy/trMXizAn9ZNVjpsP5a8knEN/LJOrLqABMmWWVjzB7aaQWEdpya/qA3DbU3Mb6qpO2pHl4BSEELXSqrKBDwGGu40Tx9OUiBtnuYHmwstXg0f+uPHR9115LRW/rtDqo2DHEZYEkqg5P0xM4q8hATNo7wX6l6d+hJ+Mi1+g=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "D7dTwhfK3Y+19DOm50NXcnSXvwT+Uf9s/WuwIQpxGZ3vC89V+dLmDv/UOWj3uli1DKJoBBg9duTMKprMBvhZusT6N3FWAiz6jIMfMPHduNPoaJheawU+ogiVx1+dNjJs2S/JvAZ17QTZw4a+8zuxfbG/rNNha8RnQcAbCgW8l50oxD7cSP2h/LZ1Vwy0ytNkTlFko+JSJXW5q6nGO5FMqKSb4gGmQnhm+h4hxY25llA8fomAr/ML9M3sQKUN/iLXccVBO81qLicpgemEZ0z/Yx82hXOJlruK8rJ5vC1DSygXyDfn277jtcl6s3+AjMpNUFMtGZan8MHgxChJX60ufw==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "4P9X33oBPKI7yholAsYI3r4YlHqKUS4/qsY+NGsfNMI6edpaG/rle5Gl+Y3WQyDIpSaH5IJAYfvWB5osqWLfnoobT/Sm+pyQD8vdkMDcmdl0pGB1VvM8oseGkkcicfW816C3LaIiKk5Ri24WGBPuGPZ6cH/opKGGSIjtRFJsUqajG/fCQNwG367HwAA2YfuYHyIdcQuIv7T1Kb4y0ML9RwH2UCrYl5F8052fFuqhEdPdPF+ykDafPofdYu/ZiR1pj3l8ly9k9vceWZ+cjszPdS7kHrSvcJ/EK2fWpqBpcRlxFObU4o9z2443aEjs/7BGVDkXHLzyVICdVFnPRN6QO2td1rltOMY/Y9JDJXYoK31scpX6JVos3bqOQAt4w17h3i2lcL/N/2WSzzqQklJm6BuNvXregtLLD6/LBhbqgKI=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "DVYr6t36rwAN3GfiXAKusr5KVtorLhMeKE/rsqNiYGaGBkItpgEpOj912UUHJEfchPxthY4fn8agP08yHmZwVQ8WHU5bs1sCURnNpb1piQaH+BRp6ndyIe1pfPMDgtyuh0i+3I/d2BtemmDAyEneGskYPN8FtEuI2P+nvkanCzZZDXEZdf2a1jlrzFteaEY4MpunGoflZUPs6hw8ogcVSH7XwpyMpdpj9b9W6L7uYh/PBuV8nJfjKi12gBIdRw1o+ydrQBNCGWZKF+sZvhGAuExmPmVB8kuLhLUv+CQMLEICab93HS8WKuhtTI/BcL3fCTzYepKEZek0KBRKXzIBiA==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "loseEBAb+DC9rxYFsK/022N9Jm8pd5646MwJrvXGel0sP3eRytwAFCtiwS2IFiQvzrXbXsN3uEfidwB64Oknxel0u4mfKC81Gh5j+BW2afieZEdc8VN5q2bS0nPEH2BkczY/4jTQl80TgBKVFlin9LHm1ITGDYuVGdWKOjawu08p1Kg5uHO2L3gZY6rE/yAd8n8OQYVluOgsRLxMDyn9Im9beHrHgTTXOxDqreBHUX9FHiSjbup+bzwtONNJeVmGp/uwCikQg1sC0cyHBY/VsDoTOExTf/HsAyTwdNJLaWZWu/zPQ8mhlSD9NLTCMggJHE0QMQgKhUTkItu3F+ghNfFUly5iP9Rq5GV2Ccw3MHbZxhibMfSrT5wthbPKHMiQ9eI3MeeLdONzKvK00m3YV6ZdE8/QZq6x1tkPGfXDJUQ=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "Bki/0ajebY9VsT7wahQI3LB5ctoa5JJf/KG77ec6yqPY3H0mF6PyHFrtG2GhNnW3r8JZjERiapOsh+TGIg70pHW8hty7WpXJDR500ip8PV2qROwoPpBVtwQcgp5jvis3Tdlt7qpGijnLRus5/ru6HZUFhBi3ugKeJPAt6P8ClW/l66xmMfo1b+N2uYkB0+p01Z1PWwy5xSB6D4rXQxtuIpweXiJQu8mLXTb/ygLgZLreF9zLn6CyhZpyBcbvGtILXJreSYjujvlB3RDMUDJ5lVwG2HNOJTTb2lvusWMWOUUr010aqSXsfv0i6NExngymRMFzL1rde6/0zMPy44C5Sw==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "KmQ5DE3A0p9plpMWyx8Sg3YNyx+TVB/Nydbo0ep6JHbMdB4nLYVxamQ55G/3ojolNHAnIu0cf4u6v49DC+uQR7H99a6kzghxcIxJiUD4Y3R/gNUROcI8qpb1F1N5ZQfVWd6S/MeB9as6urIUaTzuDP2eE7cltFkz7b99pEHg6yv6aeZmVlBvFi2TTSBvE5vX/7wRGruYHYI1MUvHP+1gcbdId1qhSB/bu7d6j2LcI/kkT1YbE8u2+AdSqtuZ07mKDPBC83+MEXQDtN1KUZJN6eJ1H8TEOsjJmVMugefNCr75v/xQOk/lIY9mzslJwywO8K1iCN8UqnZA7pSnI8DVSIa/kF4wFZSbcpmioC8P1z7r5bm0YN6kk5WGXkpY6fiv+63FqUYc2mTpM6qprir1gRQzCPc0h2aY6fKSGX9nYsU=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "JVY6+YWHTvFImCE/WEvpeT823PCcIvxkYFQ5fVDn3nGhdLj99NuCHYNL2tH1UQfYkikoN6ThSvvcn2nqGwtigJcCQ8Q/rLV9lZlkO36EDoxFQF8bMDOYbGtqKE+2QWyHetRYKZwL2r/FuTlBvOx1VcNyzPVxU6Uheyq6ny1Ygm89fOyZeVetfZQecdFE6iPAVmECfjOr5evXRnOWXsWvn0QDPJc4ojQcbKzcQAcJFkjw5tA7pn9gJ2pZ9Ac9JeFFpLAmwWasRSGJoiVGrpDUzeRVE0lKnDhQ9/XGOdz7DYs8hqHUyKJIIuADUFp204BPyuSfh6I/HOsUDDaHrSl0Vg==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "kz8cdWBZcVKQOk+ClRKif/w4mfKrSyEFS1tp7f8o2atWLZUpJi0imf4KPSO8gg2dXRJhbSJYJKufwlwGrsIL/faTHyBtDU1rYo0psQ2ScsN4q85W6vzfUeKecudrLOZFubNys7VOqcjqUOk0Be+ELeKZuXhhnQpnOK0Fcd1PHSj2dYj49kFHLPrU/nZVBi8p6YQJ30+0Zi8FeDMaWg2KjneI0rGkDNPMvae6S5QGzaJ/LiiTnmOSo8cjKgoQJ15b21JxV9a6KYdAaQY9GCJ1dWouWhUT7+8aIV/X/REfV7IJN7L+mOYJEXVS1o05NDHCnMblMKJIlRouu5EloTSc261hciHGZBptn64N2qIzRMr+oZsgkEDCR6EHVbTh6acs7C+Qy1A7xvGopcakNCrlKkTZjSRwBrInTFFinKKXr+Q=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "hcCX+mkzicVRPG81V+aZkLFTtdEnjn7dtxaX1ZRfW84ImQNa8AwtLEp9mhV7f+5tAMTMsNuqK86Re4sInPOLWEwc8gt+E5nBoblr38CmmjOooJeHM/VDdXHaDmcal/Eh4DV/iboZ4hH4QO/DYdgdH0eKilbSO1DKyBlbA+yZZ+STlYAeKRuHzMl8qD4mnU1mn4mkNojk4y3Vsqf+cVv0CSCJU04I4Oz+RgrN2U9nWZM9TB2PDESdEck1BgL8EjX+hahas+ykfYwBFbTN0CY/gClf3nmmlAfCldLxEJumAlhM8oPyjQfZ8Aa+z20CtyeLn3ai165GwuQ+p/CPEznVRQ==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "R1+UyZ9Eu83AdOgCApSt7t1ozxdXS8jTwnbJC2xmrjJe7N/PAYb7+DZe8SnrLrpYnMKbJEmIUBdmXS3J8AESjP3qFY/2eTUss0Urfr798x2rHq5GBx/w09FyOYGOofYRuB1FMU4FWMLg03IG8vKMHEI3oa4M2VLbwTDoUynSsF57xXNN0+b3VgHVWGBUKxwgiVin8G7K3TcHQkXzme2v3dk/XT2sIiKuwhf6KXNvwAqqPkAd2cjc7Bt2B+5NUuqapXAcKG3cqmnH5uaTS7UO4Ir/Zm92pvXTV1WvIbjJ9FSvk1uD8fg7QLZgYurjuGlW3RGB6FBTaQ1ec0QM+cVtspH88ki86Nt06DcRP3IqJn7tpnDesJHzwEfw6yWWmC/wQkUwwcIpE+bysxcC66/h4zVaalWuBwNW0Rh0gcfSN3k=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "bEu61mpcSiTc0H1h7bWO75sAb2zo/br5AbvvkJCCC+gMZjbMRhP0MCWNz7OzoWVHDtsOlz8AZHfk3SwWd6tr7DqcDUihHDy376NwzHQE0tHNeAWX4bHqSDNbaWw3LcZy0ZxQURdbzXjUNbeTW808GI2fEfotbJMVsFkGfJ49EiperNJF/8j8c9cqA0Ag+HSmnrE4ECYdhk19BzZqDBPz/1CYkooGpuIBCYR6BbJY0f/nWu6Q3DhXiVCn8E04c0W6PEyEkujIHfrgyjbe0AVKhyTGDv3/7bUZNikAnSA62GfMF0fe2DYbMdvem2HFT+X3pgYboLxJm0r6d1yCiNYa3Q==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "QHyBADwx7rCg78UHGXKjrkkrwHGXstUaepBsVmP5lpwJzsgzlRUcMt/fDN3zk4YO3+MgmHnDcxIl6MUKNU5BAFKzSili2yzNFq2MjOlR/iTNj4+m9ClzdcGwb+n4wr/NfwdmcXkvL7BkbdTz3LvXwiGWjT9WQ7DA8Jf/XEYo7CKnVInuLm+LIos/w5Bu8sA2QAnoDEcuArWcYCTFnR8CUIJEzFwbmp7GCUc5/X2jYVxcq8nRWqVtSggYoWgeDra+FDziSfQL99xBdcmEzHs79eMDTW4pSf4uDFG9xWKrZyOm3ri2M0kJtqaN4SufW5rUBbbdOu/gkWdV0HOn1prY6J0RAZ5WBBivWn6GYxJ/LbTRGXCEbaUXlRzKiT9IWvD4alHAhTjY4B5S6ZGbCWIKzGhey33DY7yruhLw8LL64CE=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "RCMjb0o09e5Xr8bBS21RkT8T6IzwdDVPqcgp0wABxF2Z7HkEUoTlUgkhZr/dDZTmB4HpwQ7VnXdOf2RLrB6NNBonCgEA9pjFtcZQvNRXEMLOZPqU8yKNfXvIYVMEk/peKDMcWh3gDwJCpxdFpqvEzoD8S7WxcJriB6SQllx8xldMtPvVCUJjJqKI+E2iEZl6eJP3vuY7HC+VXeLoLa8xXHtuj68hNWkhtX8mnRtS6mNnY8jkfx4+AAyF+dOcU3MsPlecvDvIBjqmueepTeHoC3SbcbZQQrJ2vaR9BFLPtkRJh7OWuyJ05DJbgQu519basXaGGC7l/hBtGofj0a/CRg==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "a9khP5ikDwI/C22ghGCSGjEXNhqVejUyUombKFkFv0LdLjvD3+ksH7RzYZ+aEDLvY0iwHFr+Orpmop0CSz/04wgezxkawNlKsteScySkZFXhb2PFizHu5dwqvsVvAPWbrcjI8USvv6CPymXYls26snc3j3L2y0K7hdm8TgJIEwFCx07E0TpuqxhKXDFoW1l1hellGOJvJce2/MGA/ZLp73SIcqpCUPxsBMuRpBoBiTCZ3sctjbhKO3MySsK4A3F4opDJTEIJ4Hs2gIiPklApv+nhaWvmMYzxThOG1fHVb+QUO+s9Z2h5wWpbJZc8Seq+YjBz7hmSWxX21fP9D+UVALFgOrxWOMC0VkUkkfZlgiS6I2af7WLEapDL+fLHZYataAc30CmZUF1YInVOnq1LuRE++gMMzWyzfG6KqYCznMk=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "cYMuMLu/mC0eEClABvZc5e9zH2nJsl8j6s+kpbanChPiBhqfdNMKw0M5scz7rRrJk4O1a6+816VFK1bwXvVZzllCiHYIQ68syZ8mW50LkwE5PGI/N+gkb+wfrZXm2OTnVnoRPtUePPS9cGigHaP9rR7ByqgFGOM0PGoXDwoShHnl0MyYBwgA+lRXSvN2GcYW6MxrTQHp8NuN6WwdycxB2RZfYF1di0i2hg1Gb5IOgL6K8N36c2IA7G3+cqLIwJglvn4h3yZtY2MPqqvUoj1tgWNJoRFCWwIUXU9EkHyVy+CEFHJCuraeTKIh5tksTgTpzfcpT3zgLPhLScQgtIKb5w==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "g+56u5e5TZg3sdZY1M8pt+HkUCPlQ9bH4vwgoPf3ldbd0uWBOzhXPEKRQk9Tq0rwEg7OSac92690xHBOWYM2TvT/yyPqe4HYk4aJHzqW3XX6LyXKI6yOh5kbG2zusYjRzSwJqft6QvJuwfYtYBkxYJdrgMbaQMz9qhCsx/VSCCsWwSkcscLDLfN+fT98tZTqNDOFKxoBdBgyMTiczaf0xXkiliMYNfV7TAckH+N1S1pVIrXQMMXR2URfvjXeohKbGwyUSS1829bUEbHGrCOOOWnG35Aw1VEg6qUaegqDJA1wlDyzV2qAwBT59OGVA23DbQUNkGh5D4qBIKaFM4n8r+6g2c5JgNmbkAFFNF8AS3/R3ZwAR5Ta1Y/tyyw5LJ98DazZog3OhhWCrxNvAzpj/qXDyvA1uYOHUkg3qndoKdw=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "PHdi7yFWBa1FMWHSMUkRuO+Iw2+e8l1ImpyW7dDoJ0yK179IM9O687YSqsj7XkfsHbKb3gkB+PYFL3jeRQqOJ2RgsMltsR2UlV8vDjcfRes7wvMf17flRm/N5Slp5bUxDjV3Zn2E1afBv0gyNb/h6AKrIhAH4X71ycCCyVJ9lzNBDFpE5umGu4hbWhRIRvAj7lOXGELQdHVIIaC8G4KbvQQpIK4uQ72zRSh4rS3ys5vudOkwjBiTdTG/ccThZwVHGwccOIF0ukfQ77AzVZoA2Bs5iSjkeRgtK//ATvLPrm6vteru3tYcI4IGIrvT/GcJOVKgdW56a4wrmD+FQ4QeUg==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "+vlYI5I8LK3/1kpIhyMq29ebgGgQuOl711nggxuo4emxKfq5OS+lhZ69ekbHNa2WlNhh4ghIfJGXpDwNURnTB4V2RekfT7NZWz+hSewsoYSBwsYRA9qp9CXAZBzSI2m6fjgI8+rP7fzjTbjnXRGM7GbNGRVTVGHQ3vfmsgRf4hUzmglX51i+fz7Pjo8nbldgAx6Zt14TVL392UQ/yrTZEraJcVZHwXTf0nEtpUNa+nbe2+gtHHuWKXxMu4BRdi7MYH7WA0eDslIKfyoqYTZvu0PsVTdtazoLgPpXdM5UVrZmMWIBSA4SXqu+8s+O5VsJoc5HqIVEgUI+3R0XI2aoMFhJBEKXN+4lUQ6rtxBlLK2BeTagz+K0mErjKUDRg9GQgr0dI83RymS9TPBtzCu2jov2qFY31nm6X38nw/jh6w0=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "KEH5gq+cNlXkphETnWj8GhjN82u3D0nHAzJl0eqYfCB+aUxacxmUcYHaDnBLhK37531xBUF0e5/s6eXKTeY7aL0u8d9Ew3ruGVDpAA2gu3gQZHzleV4n3l2elCD97A7GvuEMZFwQxHY1ydih/vthrBZdTNvWs5ur9FIsqKRDfAB9sf/MivuBmqSwWo6Y+p5bzKQW/dDVJ4Zj82QSPBEzjgx8yuUJ1iCejqLUOpvyVP9ezUJBLVFGF26UvrsHkz4QBnpX2uO9VjRmISjxk8HWXJcpnSdRMX1v0uRWYmx/bi5ocI5ii3om3tSTGtPiEb5c8lg4Qp9pEKwe9xR2bFF28g==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "KHshx3lNtqbkH1yY/4kMYmj3SP46Oob2cfY4lOmsFii54c/xIei4qTPWFZe5oMj7r9IR25vtKFUTNvD7rppWwJg61fEfBlUOfAHzt1YZjjg+OediycKzuydtQqq6RRRA2569WAo+01wP1mB7p9HtTvJNwoT1LPuNXcznS8o9h8qnJvLZnfZNYmgc7AuLtLtaqCCEHyQ12HGteglktii6X9OsV+v6mwVq2iU+xgY/4tMiTeU+WpyUuEntGfEnYc86x6XJu2i2wIea0cBWfF70gYtrqCr7HuauySEEQbUttlOkWXXB4pz4dmxQvjYrePnC/EymAkA1Zp4SghMXsQ5xgDuiq/LNjc/8rno/ecjizhnGKv/PYDMUUeFhCoerRQlakrl0ro5PnaRilPfjsZfwC/3S9BsR0CBnoCahnl+yclw=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "YZY/MpIho7mbThDgiI8WnVS0mKmVTUvvlyrYL4r7EUWsnyvxA5gRXYdbDfumIj9t/PcrZnaiNR6Qe7aM3/uaVaUqHnuiiuqIe/aV9eEhMRzYdWgMmd6uvXIFg1xEQv05aNZDyoZytVZCMd9xd/nubCgMlqj5mzhQ7FZsFuOippEkZYMKehxatXLk7vvG3TsQCtv/kBtsyv8ZnVzmhKWGugywrNqxthKWcPRN9RYJKnraECio/Q7+v/Z/2bgBxEcenp4AdDustfIOW038tPAb6+LcOytooSYBwPMyHX85mFq6DeZX7j6ms3c/dvVq/IWxS+rxSYeww1hsKRFGyDSPDw==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "ZPjEUfXpNt087ZmJMm+AFXMh0sTSHfzvdR78c36YUlKbb69PoAmTe9okpagiKxRe0ugyBLLl2VotVoyALlqGzOqNLT4jd65BYaDtkMB/YDinpjk2MJlGIlbs4M6w0eze6jIgoyfLV++xptOqJN1n+YKJQ8GY+eEhQ3Kg7ycTtTX0oIsY7tchoqsgFYRKWJ50sGwWwneGfkEY4d7NvTjcgb5QMDYt/FxZK2fXCFCKkqScne8HGaZLrEajBx9nK7vSvuBPTqfF1f7eMfK/GU9/SbmfcCU1p59sXVNrayfDlzMhSPVoJB4VVU2cegoKrfVf8fo+9/Q7mJNgjF0J+0eD+01XqvPq06qlLAsPeSUcRVDJvcL1Dsd0K+8AQirhp6/IaQnyyHwJ/3kFFvBSsp2f6i/y+7NIAdwkpdoBtWIL7zg=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "NfaOFDlHLhaiMdWYbMQUBhFi61ZRLCaAeTajr9JXjBHCFOiniLaiYaKAS05KF6L/Eh9Aq9qnADr31Q48b9/NT4NqWMFsh9ll3rZISGad3qJAfMXmPI6CzesUJ98M/eHOhmghaMustkKf2E4FgMXCBfVL6/rAzTj+0tOL4xNiMrfEMhtQsj5G8ndQnL12k2JKjHExqoyeDXCXx6vRnYWGMpeO0eSC7aeOQTvvT/ktM30FDoSpLkLksheJpnJe5QhYyl7u8473IcHVEOASN7K+mZ3boziSKjaFqtlmm+Cs4/lqZgBJyuw+6g038nHyc4SPrOsLtptb4FAzQdDcEuQB9Q==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "5U1b5z3Sb2ufZOkgkFkZDCiXUgyh/EPDSfN+QzWPWCFlRNcToJBejXNZJGVoeHC6ihEJa433u9D8AZm4Yaj5yOxhkAonYaTiCdtfhz+WEthzWq24T1SCpJ7Uk+fxnRdXoFjJGtgeQmlbsfeE5VEZiiS4yYxOg3g5Cirz5B2MgVMM4aRFXKQiJHjuSI1jA+uQ8Zb0uOct/+DABQc8YLfckHChdVsLw72PPqNVNAUUm+GULo88WZam5+UkdySoi+OmLg+xyv5y/Ps/WoTaa46ZQzrL+ST8B2V0x3jL4EjfjTY+B5/xgEyBw3w4NMRejnE1in08V4Z7Ka9iNKbOj/nN/0BwEPCVrkDrGq5C+Lt1Olvj8qDQzua9wPRD0dJ7iOTc+ZH/gMdO79cZTIsU7yZxEVfqK1u28krtJdLuClHmqL8=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "Xxj/o/rVEpAjLB0msk5sg+z+17iXiPTTJOXHEAq+s8NrOkUB/xstsgagZFNKmX8t9RAgMmpawBVNmsU2UCD+V4WHhL3l5InHRp2F+i1e7rjwISUu3F6iB1H5rOZirokQQwMHPZ0YKvCPllHt57bUL8GDPOcD57AaCMQRWovyPGUWZu71YgCXgWTlLjXm5dAOnAAyBAHPEufTUXZvnf9qnJ2Nff0Rkz/xdatI91LsIA9P0SoSR/beFcqopEmP6mX6TTp7yOmfCzztO7i7bJMvRxE1i/E270eBDbvOpvIQ8S8yZuIRKGsAh01CC+ECNlfSJtnX6kULfOm7f1RjBXDRTg==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "cbgRfQGeR443IRG0UB+McKVCWd+Uiif0XHwKPasD4nRWf1zX/SH8MS5p2zVxgcv0ofzlRBOsoZJwTwCLGr7P/do074UnTMHuaq/B4ADrzZN7cKJav5ntifGH4HltfTpagwqXfxLYO3elR/9EHpW2UE8AyskyUI4u/rMAey7Anvc41Y5kflwES3YIAR7PgEtWdJTFGiak3FZxSgWxKMFTXmEE2/7Z0nhcViLAlfQsqMqZ9KzAmQcv4EPRU2ZVyK2hwKPsqM/e1NBJldA2cXZQWzwsqzCAQ9XQMRIg85D58fyzrW/fDbPwE+jCJY0aM/k5MnYFwE+63yhWuWLcZ6MaDUDvoL9f3rKQBNnVcHxXuv78X+UqOOzr0kbzfnJLhQRMVn4aT+p+bzVH3F49xYvi1qlg1bHW46g514Rvpf380Es=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "T8teNcEcYZC69WOHn7vSnB9k9CzB1q3htQnsSyU4It1XUXnQZPY6eZbpISSIjoUy7DM5vC3KRqRfNRbYSbz6WxSQwHwoXjCDDHhNpuwgQDSP3bX7CnftdMOSUS7s5Xmt0/11uXxhJw1zoqWx+gz4SkfX4Te+rNNGy334tOzG33dyre2xnCRnoAGdxmh47BNJ4UEBVCO9D8LdMPiwuH45/Lcwp52MB45Qj5/mqik7s5Zh+/VFBpBVcQECX8c4OhJvjiECj7oY6UUj6BlzbUfDSBDEx1lTfFWPZY8kJREinmJaGyYoOb4RgI/Yhyyqi8bRd6MG6AiPVnD8GBAy+xh8+g==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "tFqnYqxeYiNp7xpaIhUGzknIvnkwOszXNp5X91PM1RJAO1m6sawsPj6mYTS4DWjzcqlkSgY9mss4Ov2WDdSZ0MvFeQuBizOoq+TSWDkrAFzhowwZrChi0dwJ827oPnXCKYzVf3XFJ4zHcNtyRugt5851RsV+mRwjE2enqQ+0N6d/Qh20ilqNmTNBStWq5oxDckFHEQPv5NN7bBJnoQ+9vzaL+NRR/simJOLnt1eVvcKx+Eed2cZdReESGnUFtJb6tYmwYcoCC50gHxayexB1A5jF1LUyE4EsW9Psd25uE+69XdITDkT2440Yrj2Lzpaeu2UfkU936Bp+r/qezZAOV2ozV7sUC4tSUro3/etrXYisxmxBFrpcMfXR9ZEYC0SY2O9ySOhHnUu5J2+NyQJiqMPnxXRmavC+VD17BxP92JI=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "HFEDLKe18Xwx9DGnQldYUtK2snFs93F/YoBy0ba+1aKA6Z+pA8T20x3AWwTU+0YFeide2wbokHySAwlt3QqzVQigcu2gytRB0kjCA84YYCiQDwA4bBGmkjBZ9iMj85efMsp25qCLTeBJgPsY4qDRMM+2bzOgoFSLTTAtA25CyfV1s5SNUmu+YLJb+HxrvzQtxlZ+j0FJU89zuV4muZz+KoAIdUIbH6RnrZjKAlM0lujk7JVGN0hQChebiTvAW2IdmNLIF5P8JWa3suQQJIBfd3P2b9A4zuP0sqfLc3/ONIWxzjGIB6Tj9GfIvZWAUm9dKPFc9RM29GNuSbYbarj4IA==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "LtSZ4HqZOlfSKda6sRQhS9b9X8+sH4OOKV7P+ZV9IUsZM+BuVfFAiyl/uagFVuhZ4C18KcoQESP3KACfhWw9NKx4J0RLZg3OBLB/hupvjsBm2LTJhTZmOoeV7SvvHfL+UsDYqzE9PzjknR4PlJI11WnQldDpd8MIvS9VCMj5otziaHygypAwsrt3qgucsOH3hKOUapbY+fwrMmiUMJ6p80dKjIVH1yGWGSfEB2rBuqvUwts4DkT9JlRI3CyjAMCAg+6tbstuw3gKJaRk75I0WsOgF1vQ1CR/HXzMdGNVPo9Bkjbrz81Lov1gTHPSE8NEaRNkwdUpvVmZo08d2E32vsNvb0nfvIK9sKC3i+yHakXhIJLfk4KjGlxHttH+cPsnQq09GLn9f4hA0iMBiNNBlpW/Y2B4nr2aE14e53O6ISQ=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "CaFB5NxA7OpC4EfuxxF6UxakmszlOwaOIz1X1J82FmDgRVUz6FcdH08zzsIEL9bFdJ/0cyLzjVE6q3xsilEKKawqQ4WNCT/7Cl4Pfp3Z9zM4ytT81cCj/ggpl2sdGxmWreczKWKPkzuxVW8UcpWa/sQtvYN9oBc5qIAtlNKNmt0Z1aj1U9ykbzLVRzxZDA4MaHe1xss83o/8NyTPYIZqpGSMa4AmJf7NlYEs6ChzrLzfp26eoWNLKXZ9SWCry/8WK6MUwdFe9GPeFIFY0Us1tDpdzse48C8SNy5qOtMioBMAouplTOz7Gbg0yi4zbheuR8GQ8VVCoavJBilEe2KAjg==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "9n1l7hXRWVkLPgEnEwqlCq451+huxPc33uJBhs7OAi3z1WDODgyR9Ap5SMVEEL6GaBpDbYfF8JMqI75YypXCVyhuc9CRrPtQpMQSb28m9Od+24+SAg1sNS6lJOvaqWf6hf+jCCv0slki0cIUxFHNauGZ1VSegsUpCi6ZJCfzp0g9Rqb+Qe4pWSFrQ9hFq6LO3qK4t2Uyqc29Ebb5IbpWCpMJ9XR7U6P+ucIS9ZZuHkFhW52+ua8bfN3pdC5nn+50/ATsAuBidMlUIHqH+JuWmciRmzMnXL3GMmuIKsfpmCHLuxhby8QleCVvdFmDzb3kZDmmRGBXISTuQLN7t0N49rDJsUUk4BEy4mMTSw3ajn/sEXJvmmKRBepbq6XKOAPg/0BaJ3zV8UTb1IGG80Ob/Kc8ufdC9q/FKC8rmZ+TSI4=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "hKLThv22e5C04ABw+vaxMFL7gSwPiwtnabM7IN5Hut0TsUV5dInK2JDz9yDzZT/kKMfe/Ql41CSwckLxtYXcPBF6Nmdh99Bkf6k7XysaC+ieRB25aToYPWtm9Z9iels3OlHMXgpSkUaBeN6UAYLLKpMqO32ML9gDGU/PnuUMqm5FP2A9yqpAftuh8vnzYJJvAIgiJmIFyxLobohFH+BXfSU6YxTxDfW00lgU/XwApFxKPYKUkDrxlpl9l1LIlwSfTMNiEzncGtHeq8N5fqVLasrI2IYBf6UilizlLBZpNRe2ar1KNMt4qksywXin0qPLbZF6dct9NpOZ5JFrA9mSVw==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "TlSuDtD2l7wevaxR05Jqie03Lx1DGVJAYLOf8gg/gafbtCzt4hfKpxyB/gkOQnY0OHrQAsC0RiKoH22kO1/6D2XdUV04/2YFi//rY5xKbDHYSRYmHri4Wiyx032vVxKIamx0aqHYZgadFGyQjm6ZhGj4jd/W9vJc+aqlB2Nbmx/LyY8lPeDHAbvktTxLZEzi1WlYHCXBaFRQ21bCcCxhvJktof/d1nmrZ44vzlo5/f3VfHxBtbWwKdaxkDms5e08b7e0g+WBQPHMU15Tje3VZ8EXos6vGMen1ofg78+ZAZm8edtlnHl5ZNn3Wf/0BcyUAi6FVTUvtnzw6MS8FALuDjuVP2Qn9jm5Gd1I7uZYtwN5lx5EaRMKn+Zg3274wsIhsn8RY3tmVt+YyKYcntUb/Fwzz4ih02pOA8h9TeEgvhE=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "nd6WcGQZfSPtoV9qLekGhkjIh7Ma3Hi6Hr4z4ul1cFvtOPuIqihGXPkX1YtSRUVkhREY+Fzc8ngesqcE44yNlwaBkmwecnNJiq09Uvts3Y2oYMSH+MLdzEhNsihNspudyx0ZJ/fUfmQzgJusft/vVPWxMfkh3ITGhkMb3gzKoDuoPNVBtJl8FqCBVPPM/aMdXy1tLK/iC7ZwjMx0iTYEeGzFYTjDSP6FBGud11wOVEMAWprG9AL2134IExW80T14FSwaL+YiZWWGE9y/aXZ5x+2/KGh7NUTM8awD8JjXmn6RlgJ/jSUw+tprJ4p1jnzxeUCjHOduy39u/VbPVR62sQ==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "tNxBJK+CVrU9pJGZuc7hI0nSD1XXTPCGu9KxNQg6YR0tahFLEKYr8gNJorJg2kqoiUH1/pu9rG/JDCvy77x8gPqC7aoKbMi0lHu5WE5fI3IqkkNKf+k7IBfJaOrGBMO/p2OYi99kZc7UPhq6lbLK+f0IBokGN8CC8abrZ9BTICuEPnFrjImb+NL2ggwf8prFENX92pp47IhGTjK2dP8gr+vdNrwEdw8ZMJphzxxYCJZFX3G0VMZ7GukKvw5wxsoQoHZ0gPYa9bD3vPX/zUDZrd90I3SQR7ZaDBShieWSzgyfPGx2UW89Nl7BEs5vESvQ7LMPutVxujuSGt3INdLEPxFaJcqOf756oHK+n8p1US/JBv/nK4Nx7AWDgbz5Zo5v6bGIrwnE+QoLJH27D3zUUyAqsSfwWO7ZwUajW2KyB4M=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "LRq0riR1Gfbm5GKsX3/kkaRTdjNbFSVOhH5uZGCXL6TNtc6eOSieswu7PmLI6bxIfacAGZqA3nw/A777GUF0xsZEew7AlRIMCdmp+M+yBL2elANxxzgxApezRLWQ3tv0TvsbyO6dX/VSe87WFCnfvEc5MpSBSS9sR90DHDqvPnQuYn8WsvCLfgzSZfm9T5fKzmhftoFvOFQLYJEzkIeDBbxzAO239ICnVbTR0+nZPy+MJwG1jzJnZD2GyjBEfG4q6g7o/FEMl08dgM4jfbZD7+nN7wfjBICbXJV97ZBLemW2H8XvCpF6lXTTJA+zNY+nvsXgh0VTzPCHBLB5Fc+DqQ==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "mk5ACI8DpGqFhXAMuDDbUoQ0RjUQi5vhMeM5DxrUcGaSMngzOBVK7Vf6yxnpN3NvXcoCpZN32wXJH1B9RE/xpueIHEIFVppYOODqKKDDNUF+g7z4fMkopbSTEma9n+Z+Po0xCm6tFBNNZ8o1aLuE2yysl6cdC4dbP1DyfkADNP3Y4ilI6dTpIj0Dpv5FXrcDUt1V3g14kpnvXmSYfu9vFMhheCthA+tkCpKn0+IflTAFTdkUF2IvputRB7jPq3YhjKYQRevFZNUXmpj2tnpudBYD0RhEQd+Gb/dZU8LZkjmIl1LFOvpUNIezKBRk/Ts43RHpAM3gU129I05Pk7z8Odx8zQ3tM75rXzJsIy6N0HXkODv1xNRWuH87Or/6pP6v5HSc7KzpJ2VlvFJMqbvp55jzt0h1BkwRn94xGRU5TjI=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "aC98NliizzDq2ASNPEPBE9Ad9BFEAO17sB0p/dV1bgke6agw83WYW9wSDOHnw6gHfxBV/XGaWU/KapYjRxW79e3qqmxrFzPoAzL46XLfGEDk9fsGz6o02/h5HKUsQy2FJutqkZiZ3O2gUwOoIO2StMAPNQpwpF1QtfT9ShW0q4IIwBdqBlQ0emRGN5zA9hY5HnHF4+vAVnTCyNL2WBHd95PRNUvPQhOsgzPNe60ldcCcSnZPiNCfVWGy+/Kjzb0jhrFeww45eXyNwZS9Og15X7oJW92fSGzxeQgW/oZYFyxKEO5USomNSI5nQ0hcZY18oxf3vQxiZFM0bo0Jrl3/aQ==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "3RX65H3zy3XwD/rNjFrxYET9Z9eXGwazPVUGClLOkYjzA7fEDMT/srpgzBWh6bBBW1uZCPuMsGLosnMksQ2CX7j6gVYMgiCxGmxKz+zqEuOZ8ni7i5K2SuWf8fPORVtHnUG98cwUO/ViDIK/xGgr1toPMpDDsdjIKmKmoxe0BPVv2PHbLbafV3PvkLbzfMBwmrYydhX5oNz4lt4dB3bW0ja66qQxdbe9B9FdG5ZrxrlIUfmTJ8dVvphauvoN/+SOwe4nuUxTQllTqxvOcrD6Qn0PCx3GvEWBtniMWfXXkkPIu5UiUzTUHOR5yzIK+LngUDTVHIrN6WsPCWhElYmH0mD9u1WjqozqT2cD8A/4MCmhM31r4CdIHDk11CH5QTEXpb0YbUkJwXqLDx350Vrp4p2Y0gpSFWFch94/uJ4uUbo=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "jbPhZivZ5FxUQzLrCqKbDRqF2sWeM8UL99z8YnxrgZMTMtdnGK/D0FqN8hdE+84omCPV+qaxzdPK1bwl/LnYkoGE/I5d9Hj7WylcK9FrsI8Prab5p+qE7SYlDZwFOzRro2uyA8XSfRONN/bW2nJWIfAEkFim2MUeVRyAK15jYIFlFQxm797dOHrXLqrzvctg0SUvcyL5UxDAOpu+55S5PS4c8qov82uIbGiTOsg8pLp+pF3ypb3kwOtn4j54sGTD37aWLvJJxVukTEW3+1FwUs6imY5AXJLE5MB2nnwtzfJFNg2U7PGODx1pYjReYjn/M0t2Y6k7NOkJ7M7QAcHGVw==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "ilp6NEWoGZ3wCT815+99xFVEFo/oosiBhMIzgYT4WofEey3OyLlAY3O4gnsZAt/Vkio8nouUahcgvGDDBLyTClFK0w3X4OAZ9yc+4j+vjVgKjj3HivHLgl6mp+fRmlcGcg1aa75yuVELN+5P2R0TJF4l6+gaqKDX2HvQUnRrTykEGVgzUiJG1Yo0bZS1hdC4IU/wG26gN71z1oVAvkbFzL8656SXgBYumr18uRDcagS2m9Csb+7WqwgwjVsAUW8q7sd49+ewwIgIzV3rP/gLe+g1yvVwDkhtzx1pPTRm11anajDSWIqTfmVhGMcvzrPe22vL0X18Ao+fCosNGY+PYxCoOnc0fyWapEPZ18zkxQLYTt0bSJ1aKgTlMWCJvG0rKpZn+GKjtLRLLVNtd9NbZnwpkqjhWeAuio0O+xX7tlM=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "K6bI0jJbjzopnEsUhra9LxZosWhiiO5RbnXRlOWwG0xZ1NNaFuteXh/TNCwz2OrcBQVWkVB0fROc40jenTRzYz3FTCV/sa05fZMNRU75zMk0W5IBGtDPt411RoHfCxO4hnhaRIAkis9eDaOcmTpz8ZqjEAZn8dImaF9L/8uTAN+6cXgYbtRl9ulvQEZiK9opbth0MMnLZ94mv51fV5c3wn3vh96ryB8S4UnpbJTtb0M1ts++faxRSp1JdqvoKQQOwbee/lVJu0talm0oTD2giwNnzqKr17+hfWIHRjeSqKrj63zWsSk/RSTO55Kd08lTlMbDeUdJHJVwXfkOquE2Eg==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "LBdG4Szo59lZ9QlguIjG204zTWhUufFtBUon17319VpRRQ1vFBQdbwrg/1MvptCa54/zsqSRw77odLhelx2iNMHq8sQFbTMcWqCjUkFv5P5EVQa/F+Er4adDG+wHwUG+7WKe3KVVIkX6Zl0zJANPaBY4r8+o02NHvsRIwfcRZLuRcsxBP/Hfr/l51cdIpzIdut3Eji0C6XVP9WG1j+wHipkmyRGGTDc7xaYTrmoiax5xejdwbUNrehyDQFKJBcDOJJP2GrXf8zsfu86kwux+FtAmubf5bJwrpaKYkVx4kWDL0Dco/vurTFCoGAqiGB/Nem7X29Hc5xkNcerI0dm0NkVP43CsA99DFq35Dh+CxP1IVXeiTjBjyjPE9dB7ymNI4IHiCaqR9QG6NxSeybw302MkYEaNWoufweO6btte+UU=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "GiLL3AapRKyfTtwIobPnhnntbN4+sHiGgJidOmVJCdBhUmEb/6VZWwuUkGBNV8DDSuJUEt3EWKRB18Kjemr/UODsbMpXEfG8oXLwzQclrjIi7Gw/+JJiXaC7Rnfy17aWMT2baB5dh3SIezidt4ee1fbFUD+mrkxSpkx8Q9995ol7JYxAZ/u5AS6Fm4LS3c5sKAW1kS0zDDAns164nNeuwcNfg+9RpkZCN4mhf04m4KjoBp67LFvmKi0CUsxw9BuPuSqAOHVJNTVNfUPJ4B3UAo8t3IjZjfxdUsuGcLkCjgrsaY2uzFucrWkFu516M36H+dVGVhbZxjUVgyuPd58lmQ==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "0LU4OG1LXrGBoB80wDh8mN18+uuP6GPxrX4Lf6Ta29dL002RrgKKRGNHoXCJcXVCFPnT4W4vmzAQFexFcHhcKgoyqX7XcXYBQqApqRZxd+tNJHfyW70ESoOsx+xwtowBwR0nBYg6x1VbiwkqoXPa13HIhEKBSOUSp/yclBe7ikCKpJfC6ooYy8nx5vHAcu3+Z7AJdW5UtdSZVE7pizxb0D7Xy+THEaiSkR7ArA0uJcc4kpju594ZfZcSl6ayQBaJc4HKlxnbOj0Om7b7M79RB/4FQyp2zchSp+1raVT6K6P4UIq0oMuSx86kZJKapO+jH4r3y4ZHEcEzxmcFx76aH1BUNXZPRPvW24khl17ujCPcwdvcuCADkO0mELZTvXocDpbjW5ByUa/Wv96511L3Gxj/k0QuzrX1DAsL3AHEf9Q=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "R7yi0YXwNXFpsTFeRYCuSksHN7jCHd7onnwkPvs8rByxj2DNPDmYGa8Im5MjUZADU9ksRBBg7nSVhPupJotcNZWavhhLeqPx2RhM7iHJ+2AOPWjp79vc6CNnybJl+mYKFWaJF4CMyLBU1wL9SOTc6danV8aWpDGPMxCjJILKtmQNX3S7Q17Hd6eC1jwZSz4yjIiPWaMr8L0guQTFhXAEBVWunpBenfYSCh9uN/cIT87Kb+GctoIX0rB/Z0cyIGtJkTrkLIn8gO9uGaf7oLFCXppzUPfGZirKYHbSXt8C9PpKSe3Ctmug9nvP4wYY1ydvb31DHsemWar3Oy4LQwrwnQ==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "+n3A2R2mkL4lbSa4dCco2HamJ9f1bCDSz1lvoFEwoFVH0xayxvX2jihbrUp/9vS5k2fTbU+NmyI+cHnAHXQV2oyTFXpDO40rMQKeqSoZ8xzHr4PFywhQ9Np8LmmN9ZuXN+GWy+erh8vrSjDLSUMrexNYi5Y9dF4P8LdTUhS4wz+4vShV1W6GNwAICtljpJ2se4zah09mCOI3eUHEnB1i+COnavpgFB8Mqf8Fq0yDE9KLHHaP2AWmdNZKKlihBrWienqHPsclfz21ydFXLMoIX37bVPb6X4fjmJpMQiSwfXyOjRZa0o8KomVBEb2hbWaSzDFmKG43c3gin46diA1SVxMjovk7Gi0JLT89gWiffFDSGJj8+v7WrAKxAHK54SfvZq0ME5FbFO33Lu/W9ouvzeXK2oIRQM5nl/JX9BVx+A4=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "RtGeprXPZc9qkWh+4ntHKBVBFaJJN0l3MM3uT7BNZgnphoVgV5S1K/mpgNdfihMQ/fAEXHIZT9t8hwjXYlVmZv1E2Atv1w0XhUloAUsVyqleecYu8OSBNNPGOwjSQhHrBZbrQr/KMBmXfiQm/AzCrRvwiBxI/5yNQm38VsDJD8T6Usk7CjLQza2LOnD61CFSNNgk4dw0U8AauFWtdBGhZqp7QCqCpyduDeJyuyuU9223nKGK51EX0MK+WXjAn6mygP4impj/S3SpC9Vok2Xbw2Z5aUIgVwzXc9ShI0jPSW6QxdwoqqumSSht5veyKDuRIj9dOhJfvfoGHNMdCz8foQ==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "WxT+4SI+zouefJGimXxAmQRHYdkQBQbj4V6YPx/PEbYk1qb6G8AcQUnL2zTYnDnSxTPfkIKd/LSB7ErCkSykb7actWs5xLNTEOlGcTuM/HQiSd9svgH3RSiFuwzsBsw50+DXwKmiEKgHrlUUoPWCOOfeMZWMOLF3NVLxalYWkK8pkZfNfBAV2dzwncWqPEOxhAAcfjQHImxwQ4GehiXGs4oFBZ14Q+U/xkLyYTswIE3aBjIBqtWdHIpWYQjPFbFfR8R61BlCcGhwOAYy13y6NOHq0j66aScs7OKc4/A7Z6eh+MsDigd3QIiv8wjkEVAxa99LJuE/3hfuKLfgGGEs4kwf5MJkQyXdBcRzQTxMuupe9/yVjs7VgpwqNL1jf176h0RPVCi/QUWRv1msNaZCKc0ve/UpCumUQKOrd250HBA=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "aWfFZwHvJqtO5w6qakGBS5t3Tfeu3/c2xgLeAbcAoV+5k+TTnxB42T3Y/pJl59D3UT0FROLWeYzYGv14G4eOE0qsqrwnyvtNyghJOzRHSuJakRkO4g6eaDmoYT5taomcAhtUfymJckrc7YboDEWDnw2nYhnn9qGDiii0DNOOK3U7nd7WiBm6zV+vAKV7gNxuQWqTE4wZ1j4zN8G8iajsJlah0/24oUraM4cknGgCQsRWswVsTomlizmmOGqP9JR1R/0Y1o8/OF2684o1nG8dy8gzW1nME4nqIaD4lb2VUI9FjYKipSEqHBZjmr/UT5D/yzp+B0v0a5zYgSy3JS+5dw==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "qctcujHwj4siTMVZG7hxe1eS9ay754zPBF9NwX6dwyyjInMUSQP9RAI0EPL8dXpsm7kFkd/3l35w5XXBXIOLlUfIthaFO5KsNRujy88KLEtqUqjbEs9gJzTQvSjusN1ymAIuhFuCuGZI9zwXd5QDQ0kz8sZ3Y7IJCO5sKQmvY5OrPbRU4pdx237maSnG22QvfslRGDhA+tiY7UeqHjPF873eDm4SynP4ezPrHQUVGCZM4QUpruETtrpgDxOwJpGXkUqdBf2P8VRtUOAfxJiIhN7o4bh39khPaNtOVXxNLIOBbkDSt0uWPRZ64vXaworBOXvoaA3KMEfESwJDfguRpCzL7GkGuoNGWQv/KZrnf/IW2IdRmhsZkl8IFEMHmG6GwGbvTj/n+O/fFMO1EvcxiDagAoSTZ6ohSM8IEznXhjU=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    },
    {
      "U": "VNW1E7kyFgDAcvEG5ucGjPN64F7s0GuivqmqovnRYYNL+tGMRI1C4XdXJR1dd+ZwYWWjz5agZWzacYRqV0lFF84guI8ILci/mPCfMwIqXsy1BAM/phlMR04jinJLG3Hs4NsvKDcso+GdzxryYQNAP4Judsonx+TXAIMq//7rRJ9zpHNBc2S60wKVpztVkqhyKuTrMFWIVyKQPueWABFBSvJ0zw10N650KpqVvXQTIbRs4g5VEyfp/38ZxKmRKTsmT4wP/0xyJD2B1vfCCBHNBtUEl4QLQ/1Akv20Zls5ZscNZS1MmztpP4QveiNfn5YTYNXtXEVbObIlyNkJJHEZJQ==",
      "c": "AZumhnSg6OxhgFqd70HOuW4EfP3B6n4QeZpMhcMRB4Y=",
      "v_prime_response": "Fy3I5UZaC5uqLojftRKPbtEskeLfTvkRisiWjbnkSZ4qCGZAN4iz6JJGqULqGzclhoii3OoJaF61wh4rJUq4RzGZ67FDNsWVptGXcyylMdBZDVKRM3u5753S1FmgfUqwImohz5Vnz3a0m9G9xpIqvp3c9uX3TIn87Wie3iyhX5AaL2uYCO3ETEHYBNIYntMSWRb3SFjTfUOzg27ne/8t29saN0Tqko/LFa0GicnCaJ1G1H5k4WYtk3VTiAeomkxiNrbM0BIbRVsaYPJQotLx3HdUCNjMEEWs/MlHieYO6+DrmKgAFylIohAY3WR0zaKm+nHaRKZZWjeUa6B9BrvnomWG2Gu6D9E5AugEiOqKbcg+xJEcfkiC663RFtYurRJpOEkGDMzEYlb7QaxyOsDIjFg9NRLpYynAgxhL55sg0k0=",
      "s_response": "zNlwRmAjN3TujP/b1MYZyjpmmLPBQXjIuJ69vIndG8i+wz1qbFIaKpFSFDrpPwzbBiP7zr7mWKD+6948GwczM7drqE/SMo+HX7c="
    }
  ]
}
"""

prepare_issue_message = """
    {"issuerPkId":"TST-KEY-01","issuerNonce":"UslfUmTWQUkcLPJy+9V8JA==","credentialAmount":28}
"""

stoken = "43b09572-c4b3-4247-8dc1-104680c20b82"

if __name__ == "__main__":
    data = nl_sign(
        StepTwoData(
            **{
                "events": StatementOfVaccination(**vaccination_events),
                "issueCommitmentMessage": issue_commitment_message,
                "stoken": stoken,
            }
        ),
        prepare_issue_message,
    )

    log.info(data)

    data = eu_sign(StatementOfVaccination(**vaccination_events))
    log.info(data)
