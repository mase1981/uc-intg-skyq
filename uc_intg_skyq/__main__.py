"""
Entry point for running SkyQ integration as a module.

Usage: python -m uc_intg_skyq

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import sys

from uc_intg_skyq import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Integration stopped by user")
        sys.exit(0)
    except Exception as err:
        print(f"❌ Integration failed: {err}")
        import traceback
        traceback.print_exc()
        sys.exit(1)