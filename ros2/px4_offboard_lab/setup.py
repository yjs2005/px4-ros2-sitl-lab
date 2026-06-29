from setuptools import setup

package_name = "px4_offboard_lab"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="yjs",
    maintainer_email="yjs@example.com",
    description="Simulation-only PX4 ROS 2 Offboard hover examples for SITL.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "offboard_hover = px4_offboard_lab.offboard_hover:main",
            "offboard_figure8 = px4_offboard_lab.offboard_figure8:main",
        ],
    },
)
